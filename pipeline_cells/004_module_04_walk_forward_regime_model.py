# =============================================================================
# MODULE 04 — WALK-FORWARD REGIME MODEL
# =============================================================================

from scipy.special import logsumexp
from scipy.stats import multivariate_normal
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import RobustScaler


logging.getLogger("hmmlearn.base").setLevel(logging.ERROR)


required = ["features_df"]

missing = [
    name
    for name in required
    if name not in globals()
]

if missing:
    raise RuntimeError(
        f"Missing dependencies: {missing}. "
        "Run Module 03 before Module 04."
    )


HMM_FEATURES = [
    "Log_EWMA_Vol",
    "VWAP_Distance",
    "Return_Surprise_SignedLog",
    "Log_Relative_Volume",
]

RISK_PROFILE_COLUMNS = [
    "EWMA_Vol",
    "Log_Range",
    "Return_Surprise_SignedLog",
]


def get_session_lengths(
    index: pd.DatetimeIndex,
) -> list[int]:

    if len(index) == 0:
        return []

    sessions = pd.Series(
        index.normalize(),
        index=index,
    )

    return (
        sessions
        .groupby(sessions)
        .size()
        .astype(int)
        .tolist()
    )


def calculate_hmm_bic(
    model: GaussianHMM,
    X: np.ndarray,
    lengths=None,
) -> float:

    n_samples, n_features = X.shape
    n_states = model.n_components

    n_start = n_states - 1
    n_transition = n_states * (n_states - 1)
    n_means = n_states * n_features

    if model.covariance_type == "full":
        n_covariances = (
            n_states
            * n_features
            * (n_features + 1)
            / 2
        )

    elif model.covariance_type == "diag":
        n_covariances = (
            n_states
            * n_features
        )

    elif model.covariance_type == "spherical":
        n_covariances = n_states

    elif model.covariance_type == "tied":
        n_covariances = (
            n_features
            * (n_features + 1)
            / 2
        )

    else:
        raise ValueError(
            f"Unsupported covariance type: "
            f"{model.covariance_type}"
        )

    n_parameters = (
        n_start
        + n_transition
        + n_means
        + n_covariances
    )

    log_likelihood = model.score(
        X,
        lengths=lengths,
    )

    return float(
        -2.0 * log_likelihood
        + n_parameters * np.log(n_samples)
    )


def fit_best_hmm(
    X_train: np.ndarray,
    train_lengths: list[int],
    n_states: int,
    n_starts: int = 10,
    covariance_type: str = "full",
    monotonicity_tol: float = 1e-3,
):

    best_model = None
    best_score = -np.inf

    for seed in range(n_starts):

        try:
            model = GaussianHMM(
                n_components=n_states,
                covariance_type=covariance_type,
                n_iter=500,
                tol=1e-4,
                min_covar=1e-3,
                random_state=seed,
            )

            model.fit(
                X_train,
                lengths=train_lengths,
            )

            history = np.asarray(
                model.monitor_.history,
                dtype=float,
            )

            if len(history) < 2:
                continue

            if not np.isfinite(history).all():
                continue

            deltas = np.diff(history)

            if deltas.min() < -monotonicity_tol:
                continue

            if (
                model.monitor_.iter >= model.n_iter
                and deltas[-1] > model.tol
            ):
                continue

            score = model.score(
                X_train,
                lengths=train_lengths,
            )

            if not np.isfinite(score):
                continue

            if score > best_score:
                best_score = score
                best_model = model

        except (
            ValueError,
            FloatingPointError,
            np.linalg.LinAlgError,
        ):
            continue

    return best_model


def causal_hmm_filter(
    model: GaussianHMM,
    X: np.ndarray,
    sessions: np.ndarray,
    initial_probs=None,
    continue_first_session: bool = False,
):

    if len(X) != len(sessions):
        raise ValueError(
            "X and sessions must have the same length."
        )

    n_states = model.n_components

    states = np.empty(
        len(X),
        dtype=int,
    )

    probabilities = np.empty(
        (len(X), n_states),
        dtype=float,
    )

    alpha = None

    for i, observation in enumerate(X):

        new_session = (
            i == 0
            or sessions[i] != sessions[i - 1]
        )

        if i == 0:

            if (
                continue_first_session
                and initial_probs is not None
            ):
                prior = (
                    initial_probs
                    @ model.transmat_
                )
            else:
                prior = model.startprob_.copy()

        elif new_session:
            prior = model.startprob_.copy()

        else:
            prior = (
                alpha
                @ model.transmat_
            )

        log_emission = np.array(
            [
                multivariate_normal.logpdf(
                    observation,
                    mean=model.means_[state],
                    cov=model.covars_[state],
                    allow_singular=True,
                )
                for state in range(n_states)
            ]
        )

        prior = np.clip(
            prior,
            1e-300,
            None,
        )

        log_alpha = (
            np.log(prior)
            + log_emission
        )

        log_alpha -= logsumexp(
            log_alpha
        )

        alpha = np.exp(
            log_alpha
        )

        states[i] = int(
            np.argmax(alpha)
        )

        probabilities[i] = alpha

    return states, probabilities, alpha


def run_walk_forward_hmm(
    df: pd.DataFrame,
    train_window: int = 200,
    step_size: int = 20,
    candidate_states=(2, 3, 4),
    n_starts: int = 10,
    covariance_type: str = "full",
) -> pd.DataFrame:

    required_columns = list(
        dict.fromkeys(
            HMM_FEATURES
            + RISK_PROFILE_COLUMNS
        )
    )

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing HMM columns: {missing_columns}"
        )

    result = (
        df
        .copy()
        .sort_index()
        .dropna(
            subset=required_columns
        )
    )

    if len(result) <= train_window:
        raise ValueError(
            f"Insufficient observations: "
            f"{len(result)} available, "
            f"{train_window} required."
        )

    output_columns = [
        "WF_Regime",
        "Raw_State",
        "WF_Window_ID",
        "Optimal_N",
        "Model_BIC",
        "Latent_State_Confidence",
        "Regime_Confidence",
        "Posterior_Entropy",
        "Continuous_Risk_Score",
        "P_Low_Risk",
        "P_Elevated_Risk",
        "P_High_Risk",
    ]

    result[output_columns] = np.nan

    window_id = 0

    for train_end in range(
        train_window,
        len(result),
        step_size,
    ):

        train_start = (
            train_end
            - train_window
        )

        test_end = min(
            train_end + step_size,
            len(result),
        )

        train = result.iloc[
            train_start:train_end
        ].copy()

        test = result.iloc[
            train_end:test_end
        ].copy()

        train_sessions = (
            train.index
            .normalize()
            .to_numpy()
        )

        test_sessions = (
            test.index
            .normalize()
            .to_numpy()
        )

        train_lengths = get_session_lengths(
            train.index
        )

        scaler = RobustScaler()

        X_train = scaler.fit_transform(
            train[HMM_FEATURES]
        )

        X_test = scaler.transform(
            test[HMM_FEATURES]
        )

        best_model = None
        best_bic = np.inf
        best_n = None

        for n_states in candidate_states:

            model = fit_best_hmm(
                X_train=X_train,
                train_lengths=train_lengths,
                n_states=n_states,
                n_starts=n_starts,
                covariance_type=covariance_type,
            )

            if model is None:
                continue

            bic = calculate_hmm_bic(
                model,
                X_train,
                lengths=train_lengths,
            )

            if (
                np.isfinite(bic)
                and bic < best_bic
            ):
                best_model = model
                best_bic = bic
                best_n = n_states

        if best_model is None:
            logger.warning(
                "No valid HMM fit for window ending %s.",
                train.index[-1],
            )
            continue

        (
            _,
            train_probs,
            final_train_alpha,
        ) = causal_hmm_filter(
            best_model,
            X_train,
            sessions=train_sessions,
        )

        risk_matrix = np.column_stack(
            [
                train["EWMA_Vol"].to_numpy(
                    dtype=float
                ),
                train["Log_Range"].to_numpy(
                    dtype=float
                ),
                np.abs(
                    train[
                        "Return_Surprise_SignedLog"
                    ].to_numpy(
                        dtype=float
                    )
                ),
            ]
        )

        state_profiles = np.full(
            (
                best_n,
                risk_matrix.shape[1],
            ),
            np.nan,
            dtype=float,
        )

        for state in range(best_n):

            weights = train_probs[:, state]
            weight_sum = weights.sum()

            if (
                not np.isfinite(weight_sum)
                or weight_sum <= 1e-10
            ):
                continue

            state_profiles[state] = np.average(
                risk_matrix,
                axis=0,
                weights=weights,
            )

        if not np.isfinite(
            state_profiles
        ).all():
            continue

        normalized_ranks = np.zeros_like(
            state_profiles,
            dtype=float,
        )

        for column in range(
            state_profiles.shape[1]
        ):

            ranks = (
                pd.Series(
                    state_profiles[:, column]
                )
                .rank(
                    method="average",
                    ascending=True,
                )
                .to_numpy()
            )

            normalized_ranks[:, column] = (
                ranks - 1.0
            ) / (
                best_n - 1.0
            )

        state_risk_scores = (
            normalized_ranks.mean(
                axis=1
            )
        )

        state_order = np.argsort(
            state_risk_scores
        )

        state_map = {}

        if best_n == 2:
            state_map[
                int(state_order[0])
            ] = 0

            state_map[
                int(state_order[1])
            ] = 2

        else:
            state_map[
                int(state_order[0])
            ] = 0

            state_map[
                int(state_order[-1])
            ] = 2

            for state in state_order[1:-1]:
                state_map[int(state)] = 1

        continue_session = (
            len(test) > 0
            and train_sessions[-1]
            == test_sessions[0]
        )

        (
            raw_states,
            test_probs,
            _,
        ) = causal_hmm_filter(
            best_model,
            X_test,
            sessions=test_sessions,
            initial_probs=final_train_alpha,
            continue_first_session=continue_session,
        )

        risk_probs = np.zeros(
            (len(test_probs), 3),
            dtype=float,
        )

        for state, regime in state_map.items():
            risk_probs[:, regime] += (
                test_probs[:, state]
            )

        mapped_states = np.argmax(
            risk_probs,
            axis=1,
        )

        continuous_risk = (
            test_probs
            @ state_risk_scores
        )

        latent_confidence = test_probs.max(
            axis=1
        )

        regime_confidence = risk_probs.max(
            axis=1
        )

        entropy = -np.sum(
            test_probs
            * np.log(
                np.clip(
                    test_probs,
                    1e-12,
                    1.0,
                )
            ),
            axis=1,
        )

        entropy /= np.log(
            best_n
        )

        index = test.index

        result.loc[index, "Raw_State"] = raw_states
        result.loc[index, "WF_Regime"] = mapped_states
        result.loc[index, "WF_Window_ID"] = window_id
        result.loc[index, "Optimal_N"] = best_n
        result.loc[index, "Model_BIC"] = best_bic

        result.loc[
            index,
            "Latent_State_Confidence",
        ] = latent_confidence

        result.loc[
            index,
            "Regime_Confidence",
        ] = regime_confidence

        result.loc[
            index,
            "Posterior_Entropy",
        ] = entropy

        result.loc[
            index,
            "Continuous_Risk_Score",
        ] = continuous_risk

        result.loc[
            index,
            "P_Low_Risk",
        ] = risk_probs[:, 0]

        result.loc[
            index,
            "P_Elevated_Risk",
        ] = risk_probs[:, 1]

        result.loc[
            index,
            "P_High_Risk",
        ] = risk_probs[:, 2]

        window_id += 1

    return (
        result
        .dropna(
            subset=["WF_Regime"]
        )
        .copy()
    )


wf_df = run_walk_forward_hmm(
    features_df,
    train_window=200,
    step_size=20,
    n_starts=10,
    covariance_type="full",
)


print(
    f"Walk-forward HMM: {len(wf_df):,} OOS bars | "
    f"{wf_df.index.min()} → {wf_df.index.max()}"
)

display(
    wf_df[
        [
            "WF_Regime",
            "Optimal_N",
            "Regime_Confidence",
            "Posterior_Entropy",
            "Continuous_Risk_Score",
            "P_Low_Risk",
            "P_Elevated_Risk",
            "P_High_Risk",
        ]
    ].tail()
)
