"""describe class"""
import warnings

"""___Built-In Modules___"""
import comet_maths as cm
from comet_maths.random.probability_density_function import generate_sample_pdf

"""___Third-Party Modules___"""
import numpy as np
from numpy.random import default_rng

rng = default_rng()

"""___NPL Modules___"""
# import here

"""___Authorship___"""
__author__ = "Pieter De Vis"
__created__ = "01/02/2021"
__maintainer__ = "Pieter De Vis"
__email__ = "pieter.de.vis@npl.co.uk"
__status__ = "Development"


def generate_sample(
    MCsteps,
    x,
    u_x,
    corr_x=None,
    i=None,
    dtype=None,
    pdf_shape="gaussian",
    pdf_params=None,
    comp_list=False,
):
    """
    Generate correlated MC sample of input quantity with given uncertainties and correlation matrix.

    :param x: list of input quantities (usually numpy arrays)
    :type x: list[array]
    :param u_x: list of uncertainties/covariances on input quantities (usually numpy arrays)
    :type u_x: list[array]
    :param corr_x: (list of) correlation matrices (n,n). This keyword must be set unless x and u_x are a single number.
    :type corr_x: list[array] or array or str, optional
    :param i: index of the input quantity (in x)
    :type i: int, optional
    :param dtype: dtype of the produced sample
    :type dtype: numpy.dtype, optional
    :param pdf_shape: string identifier of the probability density function shape, defaults to gaussian
    :type pdf_shape: str, optional
    :param pdf_params: dictionaries defining optional additional parameters that define the probability density function, Defaults to None (gaussian does not require additional parameters)
    :type pdf_params: dict, optional
    :param comp_list: boolean to define whether u_x and corr_x are given as a list or individual uncertainty components. Defaults to False, in chich case a single combined uncertainty component is given per input quantity.
    :type comp_list: bool, optional
    :return: generated sample
    :rtype: array
    """
    if i is None:
        x = np.array([x])
        u_x = np.array([u_x])
        corr_x = np.array([corr_x])
        i = 0

    if np.count_nonzero(u_x[i]) == 0:
        sample = generate_sample_same(MCsteps, x[i], dtype=dtype)
    elif not hasattr(x[i], "size"):
        sample = generate_sample_random(
            MCsteps,
            x[i],
            u_x[i],
            dtype=dtype,
            pdf_shape=pdf_shape,
            pdf_params=pdf_params,
            comp_list=comp_list,
        )
    elif x[i].size == 1:
        sample = generate_sample_random(
            MCsteps,
            x[i],
            u_x[i],
            dtype=dtype,
            pdf_shape=pdf_shape,
            pdf_params=pdf_params,
            comp_list=comp_list,
        )
    elif isinstance(corr_x[i], str):
        if corr_x[i].lower() == "rand":
            sample = generate_sample_random(
                MCsteps,
                x[i],
                u_x[i],
                dtype=dtype,
                pdf_shape=pdf_shape,
                pdf_params=pdf_params,
                comp_list=comp_list,
            )
        elif corr_x[i].lower() == "syst":
            sample = generate_sample_systematic(
                MCsteps,
                x[i],
                u_x[i],
                dtype=dtype,
                pdf_shape=pdf_shape,
                pdf_params=pdf_params,
                comp_list=comp_list,
            )
    else:
        sample = generate_sample_correlated(
            MCsteps,
            x,
            u_x,
            corr_x,
            i,
            dtype=dtype,
            pdf_shape=pdf_shape,
            pdf_params=pdf_params,
            comp_list=comp_list,
        )

    if MCsteps == 1:
        sample = sample.squeeze()
    return sample


def generate_error_sample(
    MCsteps,
    x,
    u_x,
    corr_x,
    i=None,
    dtype=None,
    pdf_shape="gaussian",
    pdf_params=None,
    comp_list=False,
):
    """
    Generate the errors of a correlated MC sample of input quantity with given uncertainties and correlation matrix.

    :param x: list of input quantities (usually numpy arrays)
    :type x: list[array]
    :param u_x: list of uncertainties/covariances on input quantities (usually numpy arrays)
    :type u_x: list[array]
    :param corr_x: list of correlation matrices (n,n) along non-repeating axis, or list of correlation matrices for each repeated measurement.
    :type corr_x: list[array]
    :param i: index of the input quantity (in x)
    :type i: int, optional
    :param dtype: dtype of the produced sample
    :type dtype: numpy.dtype, optional
    :param pdf_shape: string identifier of the probability density function shape, defaults to gaussian
    :type pdf_shape: str, optional
    :param pdf_params: dictionaries defining optional additional parameters that define the probability density function, Defaults to None (gaussian does not require additional parameters)
    :type pdf_params: dict, optional
    :param comp_list: boolean to define whether u_x and corr_x are given as a list or individual uncertainty components. Defaults to False, in chich case a single combined uncertainty component is given per input quantity.
    :type comp_list: bool, optional
    :return: generated sample
    :rtype: array
    """
    if np.count_nonzero(u_x[i]) == 0:
        err_sample = np.zeros(generate_sample_shape(MCsteps, x), dtype=dtype)
    else:
        err_sample = (
            generate_sample(
                MCsteps,
                x,
                u_x,
                corr_x,
                i,
                dtype=dtype,
                pdf_shape=pdf_shape,
                pdf_params=pdf_params,
                comp_list=comp_list,
            )
            - x[i]
        )

    if MCsteps == 1:
        err_sample = err_sample.squeeze()

    return err_sample


def generate_sample_shape(MCsteps, param):
    """
    function to determine the shape of the Monte Carlo (MC) sample

    :param MCsteps: number of MC steps
    :type MCsteps: int
    :param param: values of the array (input quantity) or which we are generating the sample
    :type param: np.array
    :return: shape of the output sample
    :rtype: tuple
    """
    sample_shape = (MCsteps,)
    if isinstance(param, np.ndarray):
        if param.size > 1:
            sample_shape = (MCsteps,) + (1,) * param.ndim
    return sample_shape


def generate_sample_same(MCsteps, param, dtype=None):
    """
    Generate MC sample of input quantity with zero uncertainties.

    :param MCsteps: number of MC steps
    :type MCsteps: int
    :param param: values of input quantity (mean of distribution)
    :type param: float or array
    :param dtype: dtype of the produced sample, optional
    :type dtype: numpy.dtype
    :return: generated sample
    :rtype: array
    """
    tileshape = generate_sample_shape(MCsteps, param)
    MC_sample = np.tile(param, tileshape).astype(dtype)
    return MC_sample


def generate_sample_random(
    MCsteps,
    param,
    u_param,
    dtype=None,
    pdf_shape="gaussian",
    pdf_params=None,
    comp_list=False,
):
    """
    Generate MC sample of input quantity with random uncertainties.

    :param MCsteps: number of MC steps
    :type MCsteps: int
    :param param: values of input quantity (mean of distribution)
    :type param: float or array
    :param u_param: uncertainties on input quantity (std of distribution)
    :type u_param: float or array
    :param dtype: dtype of the produced sample
    :type dtype: numpy.dtype, optional
    :param pdf_shape: string identifier of the probability density function shape, defaults to gaussian
    :type pdf_shape: str, optional
    :param pdf_params: dictionaries defining optional additional parameters that define the probability density function, Defaults to None (gaussian does not require additional parameters)
    :type pdf_params: dict, optional
    :param comp_list: boolean to define whether u_x and corr_x are given as a list or individual uncertainty components. Defaults to False, in chich case a single combined uncertainty component is given per input quantity.
    :type comp_list: bool, optional
    :return: generated sample
    :rtype: array
    """
    if comp_list:
        u_param = np.sum([u_param_i**2 for u_param_i in u_param]) ** 0.5

    if not hasattr(param, "__len__"):
        sample_pdf = generate_sample_pdf(MCsteps, pdf_shape, pdf_params, dtype=dtype)
        sample = sample_pdf * u_param + param
    elif len(param.shape) == 0:
        sample_pdf = generate_sample_pdf(MCsteps, pdf_shape, pdf_params, dtype=dtype)
        sample = sample_pdf * u_param + param
    else:
        sli_par = list([slice(None)] * (len(param.shape) + 1))
        sli_par[0] = None
        sli_par = tuple(sli_par)

        sample_pdf = generate_sample_pdf(
            (MCsteps,) + param.shape, pdf_shape, pdf_params, dtype=dtype
        )

        sample = sample_pdf * u_param[sli_par] + param[sli_par]

    if "truncated" in pdf_shape.lower():
        id_redo = find_truncated_id(sample, pdf_params)
        if len(id_redo) > 0:
            sample[id_redo] = generate_sample_random(
                len(id_redo), param, u_param, dtype, pdf_shape, pdf_params
            )

    return sample


def generate_sample_systematic(
    MCsteps,
    param,
    u_param,
    dtype=None,
    pdf_shape="gaussian",
    pdf_params=None,
    comp_list=False,
):
    """
    Generate correlated MC sample of input quantity with systematic uncertainties.

    :param MCsteps: number of MC steps
    :type MCsteps: int
    :param param: values of input quantity (mean of distribution)
    :type param: float or array
    :param u_param: uncertainties on input quantity (std of distribution)
    :type u_param: float or array
    :param dtype: dtype of the produced sample
    :type dtype: numpy.dtype, optional
    :param pdf_shape: string identifier of the probability density function shape, defaults to gaussian
    :type pdf_shape: str, optional
    :param pdf_params: dictionaries defining optional additional parameters that define the probability density function, Defaults to None (gaussian does not require additional parameters)
    :type pdf_params: dict, optional
    :param comp_list: boolean to define whether u_x and corr_x are given as a list or individual uncertainty components. Defaults to False, in chich case a single combined uncertainty component is given per input quantity.
    :type comp_list: bool, optional
    :return: generated sample
    :rtype: array
    """
    if comp_list:
        u_param = np.sum([u_param_i**2 for u_param_i in u_param]) ** 0.5

    if not hasattr(param, "__len__"):
        sample_pdf = generate_sample_pdf(MCsteps, pdf_shape, pdf_params, dtype=dtype)
        sample = sample_pdf * u_param + param
    elif len(param.shape) == 0:
        sample_pdf = generate_sample_pdf(MCsteps, pdf_shape, pdf_params, dtype=dtype)
        sample = sample_pdf * u_param + param
    else:
        sli_par = list([slice(None)] * (len(param.shape) + 1))
        sli_par[-2] = None
        sli_par = tuple(sli_par)

        sample_pdf = generate_sample_pdf(MCsteps, pdf_shape, pdf_params, dtype=dtype)
        sample = (
            np.dot(
                sample_pdf[:, None],
                u_param[sli_par],
            )
            + param
        )

    if "truncated" in pdf_shape.lower():
        id_redo = find_truncated_id(sample, pdf_params)
        if len(id_redo) > 0:
            sample[id_redo] = generate_sample_systematic(
                len(id_redo), param, u_param, dtype, pdf_shape, pdf_params
            )

    return sample


def find_truncated_id(sample, pdf_params):
    """
    Function to identify which of the MC samples has elements that need to be truncated (outside min and max defined in pdf_params). if such an element is present, a new MC draw will be done.

    :param sample: untruncated sample
    :type sample: array
    :param pdf_params: dictionary that contains the min and max values that will be used to truncate the samples.
    :type pdf_params: dict
    :return: indices of the samples that need to be replaced
    :rtype: array
    """
    if "min" not in pdf_params.keys():
        pdf_params["min"] = -np.inf
    if "max" not in pdf_params.keys():
        pdf_params["max"] = +np.inf

    return np.where(
        [
            np.any(sample[i] < pdf_params["min"])
            or np.any(sample[i] > pdf_params["max"])
            for i in range(len(sample))
        ]
    )[0]


def generate_sample_correlated(
    MCsteps,
    x,
    u_x,
    corr_x,
    i=None,
    dtype=None,
    pdf_shape="gaussian",
    pdf_params=None,
    comp_list=False,
):
    """
    Generate correlated MC sample of input quantity with given uncertainties and correlation matrix.
    sample are generated using generate_sample_cov() after matching up the uncertainties to the right correlation matrix.
    It is possible to provide one correlation matrix to be used for each measurement (which each have an uncertainty) or a correlation matrix per measurement.

    :param MCsteps: number of MC steps
    :type MCsteps: int
    :param x: list of input quantities (usually numpy arrays)
    :type x: list[array]
    :param u_x: list of uncertainties/covariances on input quantities (usually numpy arrays)
    :type u_x: list[array]
    :param corr_x: list of correlation matrices (n,n) along non-repeating axis, or list of correlation matrices for each repeated measurement.
    :type corr_x: list[array]
    :param i: index of the input quantity (in x)
    :type i: int
    :param dtype: dtype of the produced sample
    :type dtype: numpy.dtype, optional
    :param pdf_shape: string identifier of the probability density function shape, defaults to gaussian
    :type pdf_shape: str, optional
    :param pdf_params: dictionaries defining optional additional parameters that define the probability density function, Defaults to None (gaussian does not require additional parameters)
    :type pdf_params: dict, optional
    :param comp_list: boolean to define whether u_x and corr_x are given as a list or individual uncertainty components. Defaults to False, in chich case a single combined uncertainty component is given per input quantity.
    :type comp_list: bool, optional
    :return: generated sample
    :rtype: array
    """

    if i is None:
        x = np.array([x])
        u_x = np.array([u_x])
        corr_x = np.array([corr_x])
        i = 0

    if comp_list:
        MC_data = generate_sample_correlated(
            MCsteps,
            x=x[i],
            u_x=u_x[i][0],
            corr_x=corr_x[i][0],
            dtype=dtype,
            pdf_shape=pdf_shape,
            pdf_params=pdf_params,
            comp_list=False,
        )
        for j in range(1, len(u_x[i])):
            MC_data += generate_sample_correlated(
                MCsteps,
                x=np.zeros_like(x[i]),
                u_x=u_x[i][j],
                corr_x=corr_x[i][j],
                dtype=dtype,
                pdf_shape=pdf_shape,
                pdf_params=pdf_params,
                comp_list=False,
            )

    else:
        if isinstance(corr_x[i], dict):
            MC_data = generate_sample_random(
                MCsteps,
                x[i],
                u_x[i],
                dtype=dtype,
                pdf_shape=pdf_shape,
                pdf_params=pdf_params,
            )
            for dim in corr_x[i].keys():
                if isinstance(corr_x[i][dim], str):
                    if (
                        corr_x[i][dim].lower() == "rand"
                        or corr_x[i][dim].lower() == "random"
                    ):
                        continue

                if len(dim) == 1:
                    if isinstance(corr_x[i][dim], str):
                        if (
                            corr_x[i][dim].lower() == "syst"
                            or corr_x[i][dim].lower() == "systematic"
                        ):
                            corr_x[i][dim] = np.ones(
                                (x[i].shape[int(dim)], x[i].shape[int(dim)])
                            )
                    MC_data = correlate_sample_corr(
                        np.moveaxis(MC_data, int(dim) + 1, 0), corr_x[i][dim]
                    )
                    MC_data = np.moveaxis(MC_data, 0, int(dim) + 1)
                else:
                    mult_dim = dim.split(".")
                    if np.any(
                        [
                            int(mult_dim[ii]) >= int(mult_dim[ii + 1])
                            for ii in range(len(mult_dim) - 1)
                        ]
                    ):
                        raise ValueError(
                            "The dimensions in the error-correlation dictionary key with multiple dimensions (separated by .) need to be in ascending order (don't forget to adjust the correlation matrix when changing this)!"
                        )
                    multi_dim_shape = tuple()
                    sli = [slice(None)] * MC_data.ndim
                    for ii, idim in enumerate(mult_dim):
                        MC_data = np.moveaxis(MC_data, int(idim) + 1, ii)
                        multi_dim_shape = multi_dim_shape + (x[i].shape[int(idim)],)
                        sli[ii] = 0
                    normal_dim_shape = MC_data[sli].shape
                    MC_data = MC_data.reshape((-1,) + normal_dim_shape)
                    if isinstance(corr_x[i][dim], str):
                        if (
                            corr_x[i][dim].lower() == "syst"
                            or corr_x[i][dim].lower() == "systematic"
                        ):
                            corr_x[i][dim] = np.ones(
                                (MC_data.shape[0], MC_data.shape[0])
                            )
                    MC_data = correlate_sample_corr(MC_data, corr_x[i][dim])
                    MC_data = MC_data.reshape(multi_dim_shape + normal_dim_shape)
                    for ii in range(len(mult_dim) - 1, -1, -1):
                        MC_data = np.moveaxis(MC_data, ii, int(mult_dim[ii]) + 1)

        elif corr_x[i].ndim == 2:
            if len(corr_x[i]) == len(u_x[i].ravel()):
                cov_x = cm.convert_corr_to_cov(corr_x[i], u_x[i])
                MC_data = generate_sample_cov(MCsteps, x[i], cov_x, dtype=dtype)
            elif len(corr_x[i]) == len(u_x[i]):
                MC_data = np.zeros((MCsteps,) + (u_x[i].shape))
                for j in range(len(u_x[i][0])):
                    cov_x = cm.convert_corr_to_cov(corr_x[i], u_x[i][:, j])
                    MC_data[:, :, j] = generate_sample_cov(
                        MCsteps, x[i][:, j], cov_x, dtype=dtype
                    )
            elif len(corr_x[i]) == len(u_x[i][0]):
                MC_data = np.zeros((MCsteps,) + (u_x[i].shape))
                for j in range(len(u_x[i][:, 0])):
                    cov_x = cm.convert_corr_to_cov(corr_x[i], u_x[i][j])
                    MC_data[:, j, :] = generate_sample_cov(
                        MCsteps, x[i][j], cov_x, dtype=dtype
                    )
            else:
                raise NotImplementedError(
                    "comet_maths.generate_Sample: This combination of dimension of correlation matrix (%s) and uncertainty (%s) is currently not implemented."
                    % (corr_x[i].shape, u_x[i].shape)
                )

        else:
            raise NotImplementedError(
                "comet_maths.generate_Sample: This combination of dimension of correlation matrix (%s) and uncertainty (%s) is currently not implemented."
                % (corr_x[i].shape, u_x[i].shape)
            )

    return MC_data


def generate_sample_cov(
    MCsteps,
    param,
    cov_param,
    diff=0.01,
    dtype=None,
    pdf_shape="gaussian",
    pdf_params=None,
):
    """
    Generate correlated MC sample of input quantity with a given covariance matrix.
    sample are generated independent and then correlated using Cholesky decomposition.

    :param MCsteps: number of MC steps
    :type MCsteps: int
    :param param: values of input quantity (mean of distribution)
    :type param: array
    :param cov_param: covariance matrix for input quantity
    :type cov_param: array
    :param diff: maximum difference that the error correlation matrix is allowed to be changed by to make it positive definite. Defaults to 0.001
    :type diff: float, optional
    :param dtype: dtype of the produced sample
    :type dtype: numpy.dtype, optional
    :param pdf_shape: string identifier of the probability density function shape, defaults to gaussian
    :type pdf_shape: str, optional
    :param pdf_params: dictionaries defining optional additional parameters that define the probability density function, Defaults to None (gaussian does not require additional parameters)
    :type pdf_params: dict, optional
    :return: generated sample
    :rtype: array
    """
    try:
        L = np.linalg.cholesky(cov_param)
    except:
        L = cm.nearestPD_cholesky(cov_param, diff=diff)

    outshape = param.shape

    if param.ndim > 1:
        param = param.flatten()

    if len(param) != len(L):
        raise ValueError(
            "The shapes of the provided variable (%s after flattening) and the provided covariance matrix (%s) are not consistent"
            % (param.shape, L.shape)
        )

    rand_sample = generate_sample_pdf(
        (len(L), MCsteps), pdf_shape=pdf_shape, pdf_params=pdf_params, dtype=dtype
    )
    return (np.dot(L, rand_sample).T + param).reshape((MCsteps,) + outshape)


def correlate_sample_corr(sample, corr, dtype=None):
    """
    Method to correlate independent sample of input quantities using correlation matrix and Cholesky decomposition.

    :param sample: independent sample of input quantities
    :type sample: array[array]
    :param corr: correlation matrix between input quantities
    :type corr: array
    :return: correlated sample of input quantities
    :rtype: array[array]
    """

    if np.max(corr) > 1.000001:
        raise ValueError(
            "punpy.mc_propagation: The correlation matrix has elements >1."
        )
    elif len(corr) != len(sample):
        raise ValueError(
            "punpy.mc_propagation: The correlation matrix is not the right shape. corr_shape: %s, sample_shape: %s"
            % (corr.shape, sample.shape)
        )
    else:
        try:
            L = np.array(np.linalg.cholesky(corr))
        except:
            L = cm.nearestPD_cholesky(corr)

        sample_out = sample.copy()

    for j in np.ndindex(sample[0][0, ...].shape):
        sample_j = np.array(
            [sample[i][(slice(None),) + j] for i in range(len(sample))], dtype=dtype
        )

        # Cholesky needs to be applied to Gaussian distributions with mean=0 and std=1,
        # We first calculate the mean and std for each input quantity
        means = np.array(
            [np.mean(sample[i][(slice(None),) + j]) for i in range(len(sample))],
            dtype=dtype,
        )[:, None]
        stds = np.array(
            [np.std(sample[i][(slice(None),) + j]) for i in range(len(sample))],
            dtype=dtype,
        )[:, None]

        # We normalise the sample with the mean and std, then apply Cholesky, and finally reapply the mean and std.
        if all(stds[:, 0] != 0):
            sample_j = np.dot(L, (sample_j - means) / stds) * stds + means

        # If any of the variables has no uncertainty, the normalisation will fail. Instead we leave the parameters without uncertainty unchanged.
        else:
            id_nonzero = np.where(stds[:, 0] != 0)[0]
            sample_j[id_nonzero] = (
                np.dot(
                    L[id_nonzero][:, id_nonzero],
                    (sample_j[id_nonzero] - means[id_nonzero]) / stds[id_nonzero],
                )
                * stds[id_nonzero]
                + means[id_nonzero]
            )

        for i in range(len(sample)):
            sample_out[i][(slice(None),) + j] = sample_j[i]

    return sample_out
