# ==============================================================================
# MODULE 16 — SCIPY / SKLEARN HISTORICAL COMPATIBILITY PATCH
#
# PURPOSE
# -------
# Older sklearn Ridge calls:
#
#       scipy.linalg.solve(..., sym_pos=True)
#
# Newer SciPy removed `sym_pos` and replaced the same intent with:
#
#       assume_a="pos"
#
# NO MODEL PARAMETER IS CHANGED.
# NO RESEARCH LOGIC IS CHANGED.
# ==============================================================================

import inspect
import scipy.linalg as _b39_scipy_linalg


# Preserve native solve exactly once.
if not hasattr(
    _b39_scipy_linalg,
    "_b39_original_solve",
):

    _b39_scipy_linalg._b39_original_solve = (
        _b39_scipy_linalg.solve
    )


_B39_NATIVE_SOLVE = (
    _b39_scipy_linalg._b39_original_solve
)


_b39_solve_parameters = (
    inspect.signature(
        _B39_NATIVE_SOLVE
    )
    .parameters
)


if (
    "sym_pos"
    not in
    _b39_solve_parameters
):

    def _b39_solve_compat(
        a,
        b,
        sym_pos=False,
        lower=False,
        overwrite_a=False,
        overwrite_b=False,
        debug=None,
        check_finite=True,
        **kwargs,
    ):

        # Historical sklearn semantics:
        #
        # sym_pos=True
        #     <=>
        # assume_a="pos"
        #
        # in modern SciPy.

        if sym_pos:

            kwargs[
                "assume_a"
            ] = "pos"


        return _B39_NATIVE_SOLVE(

            a,
            b,

            lower=lower,

            overwrite_a=overwrite_a,

            overwrite_b=overwrite_b,

            check_finite=check_finite,

            **kwargs,
        )


    _b39_scipy_linalg.solve = (
        _b39_solve_compat
    )


    print(
        "[+] SciPy compatibility patch installed."
    )

    print(
        "[+] Historical sklearn Ridge "
        "`sym_pos=True` -> SciPy `assume_a='pos'`."
    )


else:

    print(
        "[+] Native SciPy already supports `sym_pos`; "
        "no compatibility patch required."
    )


print(
    "[+] NO MODEL OR RESEARCH PARAMETER CHANGED."
)
