from abc import ABC, abstractmethod

import numpy as np


class ActivationBase(ABC):
    def __init__(self, **kwargs):
        super().__init__()

    def __call__(self, z):
        if z.ndim == 1:
            z = z.reshape(1, -1)
        return self.fn(z)

    @abstractmethod
    def fn(self, z):
        raise NotImplementedError

    @abstractmethod
    def grad(self, x, **kwargs):
        raise NotImplementedError


class Sigmoid(ActivationBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Sigmoid"

    def fn(self, z):
        return 1 / (1 + np.exp(-z))

    def grad(self, x):
        return self.fn(x) * (1 - self.fn(x))

    def grad2(self, x):
        return self.grad(x) * (1 - self.fn(x)) - self.fn(x) * self.grad(x)


class ReLU(ActivationBase):
    """
    ReLU units can be fragile during training and can "die". For example, a
    large gradient flowing through a ReLU neuron could cause the weights to
    update in such a way that the neuron will never activate on any datapoint
    again. If this happens, then the gradient flowing through the unit will
    forever be zero from that point on. That is, the ReLU units can
    irreversibly die during training since they can get knocked off the data
    manifold.

    For example, you may find that as much as 40% of your network can be "dead"
    (i.e. neurons that never activate across the entire training dataset) if
    the learning rate is set too high. With a proper setting of the learning
    rate this is less frequently an issue.

    - Andrej Karpathy
    """

    def __init__(self):
        super().__init__()

    def __str__(self):
        return "ReLU"

    def fn(self, z):
        return np.clip(z, 0, np.inf)

    def grad(self, x):
        return (x > 0).astype(int)

    def grad2(self, x):
        return np.zeros_like(x)


class LeakyReLU(ActivationBase):
    def __init__(self, alpha=0.3):
        self.alpha = alpha
        super().__init__()

    def __str__(self):
        return "Leaky ReLU(alpha={})".format(self.alpha)

    def fn(self, z):
        _z = z.copy()
        _z[z < 0] = _z[z < 0] * self.alpha
        return _z

    def grad(self, x):
        out = np.ones_like(x)
        out[x < 0] *= self.alpha
        return out

    def grad2(self, x):
        return np.zeros_like(x)


class Tanh(ActivationBase):
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Tanh"

    def fn(self, z):
        return np.tanh(z)

    def grad(self, x):
        return 1 - np.tanh(x) ** 2

    def grad2(self, x):
        return -2 * np.tanh(x) * self.grad(x)


class Affine(ActivationBase):
    def __init__(self, slope=1, intercept=0):
        self.slope = slope
        self.intercept = intercept
        super().__init__()

    def __str__(self):
        return "Affine(slope={}, intercept={})".format(self.slope, self.intercept)

    def fn(self, z):
        return self.slope * z + self.intercept

    def grad(self, x):
        return self.slope * np.ones_like(x)

    def grad2(self, x):
        return np.zeros_like(x)


class ELU(ActivationBase):
    def __init__(self, alpha=1.0):
        self.alpha = alpha
        super().__init__()

    def __str__(self):
        return "ELU(alpha={})".format(self.alpha)

    def fn(self, z):
        # z if z > 0  else alpha * (e^z - 1) """
        return z * (z > 0) + self.alpha * (np.exp(z) - 1) * (z < 0)

    def grad(self, x):
        # 1 if x >= 0 else alpha * e^(z)
        return np.where(x >= 0, np.ones_like(x), self.fn(x) + self.alpha)

    def grad2(self, x):
        # 0 if x >= 0 else alpha * e^(z)
        return np.where(x >= 0, np.zeros_like(x), self.alpha * np.exp(x))


class Linear(ActivationBase):
    """Linear (i.e. identity) activation function.
    # Arguments
        z: Input tensor.
    # Returns
        Unchanged Input tensor.
    """
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Linear"

    def fn(self, z):
        return z

    def grad(self, x):
        return np.ones_like(x)

    def grad2(self, x):
        return np.zeros_like(x)


class Exponential(ActivationBase):
    """Exponential (base e) activation function.
    # Arguments
        z: Input tensor.
    # Returns
        Exponential activation: `exp(x)`.
    """
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Exponential"

    def fn(self, z):
        return np.exp(z)

    def grad(self, x):
        return np.exp(x)

    def grad2(self, x):
        return np.exp(x)


class SELU(ActivationBase):
    """Scaled Exponential Linear Unit (SELU).
    SELU is equal to: `scale * elu(x, alpha)`, where alpha and scale
    are predefined constants. The values of `alpha` and `scale` are
    chosen so that the mean and variance of the inputs are preserved
    between two consecutive layers as long as the weights are initialized
    correctly and the number of inputs is "large enough"
    (see references for more information).
    # Arguments
        z: A tensor or variable to compute the activation function for.
    # Returns
       The scaled exponential unit activation: `scale * elu(x, alpha)`.
    # Note
        - To be used together with the initialization "lecun_normal".
        - To be used together with the dropout variant "AlphaDropout".
    # References
        - [Self-Normalizing Neural Networks](https://arxiv.org/abs/1706.02515)
    """
    def __init__(self):
        self.alpha = 1.6732632423543772848170429916717
        self.scale = 1.0507009873554804934193349852946
        self.elu = ELU(alpha=self.alpha)
        super().__init__()

    def __str__(self):
        return "SELU"

    def fn(self, z):
        return self.scale * self.elu.fn(z)

    def grad(self, x):
        return np.where(x >= 0, np.ones_like(x) * self.scale, np.exp(x) * self.alpha * self.scale)

    def grad2(self, x):
        return np.where(x >= 0, np.zeros_like(x), np.exp(x) * self.alpha * self.scale)


class Softmax(ActivationBase):
    """Softmax activation function.
    # Arguments
        z: Input tensor.
        axis: Integer, axis along which the softmax normalization is applied.
    # Returns
        Tensor, output of softmax transformation.
    # Raises
        ValueError: In case `dim(x) == 1`.
    """
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Softmax"

    def fn(self, z):
        return np.exp(z) / np.sum(np.exp(z))

    def grad(self, x):
        return self.fn(x) * (1 - self.fn(x))

    def grad2(self, x):
        return self.grad(x) * (1 - self.fn(x)) - self.fn(x) * self.grad(x)


class Hard_Sigmoid(ActivationBase):
    """Hard sigmoid activation function.
    Faster to compute than sigmoid activation.
    # Arguments
        x: Input tensor.
    # Returns
        Hard sigmoid activation:
        - `0` if `x < -2.5`
        - `1` if `x > 2.5`
        - `0.2 * x + 0.5` if `-2.5 <= x <= 2.5`.
    """
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "Hard Sigmoid"

    def fn(self, z):
        return np.clip((0.2 * z) + 0.5, 0.0, 1.0)

    def grad(self, x):
        return np.ones_like(x) * 0.2

    def grad2(self, x):
        return np.zeros_like(x)


class PReLU(ActivationBase):
    """Parametric Rectified Linear Unit.
    It follows:
    `f(x) = alpha * x for x < 0`,
    `f(x) = x for x >= 0`,
    where `alpha` is a learned array with the same shape as x.
    # Input shape
        z: Input Array
    # Output shape
        Same shape as the input.
    # Arguments
        alpha_initializer: initializer function for the weights.
        alpha_regularizer: regularizer for the weights.
        alpha_constraint: constraint for the weights.
        shared_axes: the axes along which to share learnable
            parameters for the activation function.
            For example, if the incoming feature maps
            are from a 2D convolution
            with output shape `(batch, height, width, channels)`,
            and you wish to share parameters across space
            so that each filter only has one set of parameters,
            set `shared_axes=[1, 2]`.
    # References
        - [Delving Deep into Rectifiers: Surpassing Human-Level Performance on
           ImageNet Classification](https://arxiv.org/abs/1502.01852)
    """

    def __init__(self, alpha=0.3):
        self.alpha = alpha
        super().__init__()

    def __str__(self):
        return "PReLU(alpha={})".format(self.alpha)

    def fn(self, z):
        return np.where(z < 0, self.alpha * z, z)

    def grad(self, x):
        return np.where(x < 0, np.ones_like(x) * self.alpha, np.ones_like(x))

    def grad2(self, x):
        return np.zeros_like(x)
