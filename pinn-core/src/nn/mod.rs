use ndarray::{Array1, Array2};
use rand::Rng;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Activation {
    Linear,
    Tanh,
    Sigmoid,
    Relu,
    Softplus,
}

impl Default for Activation {
    fn default() -> Self {
        Self::Tanh
    }
}

impl Activation {
    pub fn apply(&self, x: &Array1<f64>) -> Array1<f64> {
        match self {
            Activation::Linear => x.clone(),
            Activation::Tanh => x.mapv(|value| value.tanh()),
            Activation::Sigmoid => x.mapv(|value| 1.0 / (1.0 + (-value).exp())),
            Activation::Relu => x.mapv(|value| value.max(0.0)),
            Activation::Softplus => x.mapv(|value| (1.0 + value.exp()).ln()),
        }
    }

    pub fn derivative(&self, x: &Array1<f64>) -> Array1<f64> {
        match self {
            Activation::Linear => Array1::ones(x.len()),
            Activation::Tanh => x.mapv(|value| {
                let tanh = value.tanh();
                1.0 - tanh * tanh
            }),
            Activation::Sigmoid => x.mapv(|value| {
                let sigmoid = 1.0 / (1.0 + (-value).exp());
                sigmoid * (1.0 - sigmoid)
            }),
            Activation::Relu => x.mapv(|value| if value > 0.0 { 1.0 } else { 0.0 }),
            Activation::Softplus => x.mapv(|value| 1.0 / (1.0 + (-value).exp())),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct LayerSpec {
    pub size: usize,
    #[serde(default)]
    pub activation: Activation,
    #[serde(default)]
    pub residual: bool,
}

impl Default for LayerSpec {
    fn default() -> Self {
        Self {
            size: 32,
            activation: Activation::Tanh,
            residual: false,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NetworkConfig {
    #[serde(default = "default_input_dim")]
    pub input_dim: usize,
    #[serde(default = "default_hidden_layers")]
    pub hidden_layers: Vec<LayerSpec>,
    #[serde(default = "default_output_dim")]
    pub output_dim: usize,
    #[serde(default = "default_output_activation")]
    pub output_activation: Activation,
}

fn default_input_dim() -> usize {
    2
}

fn default_output_dim() -> usize {
    1
}

fn default_hidden_layers() -> Vec<LayerSpec> {
    vec![
        LayerSpec::default(),
        LayerSpec::default(),
    ]
}

fn default_output_activation() -> Activation {
    Activation::Linear
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            input_dim: default_input_dim(),
            hidden_layers: default_hidden_layers(),
            output_dim: default_output_dim(),
            output_activation: default_output_activation(),
        }
    }
}

impl NetworkConfig {
    pub fn from_layer_sizes(layer_sizes: &[usize]) -> Self {
        if layer_sizes.len() < 2 {
            return Self::default();
        }

        let input_dim = layer_sizes[0].max(1);
        let output_dim = layer_sizes[layer_sizes.len() - 1].max(1);
        let hidden_layers = layer_sizes[1..layer_sizes.len() - 1]
            .iter()
            .map(|size| LayerSpec {
                size: (*size).max(1),
                activation: Activation::Tanh,
                residual: false,
            })
            .collect();

        Self {
            input_dim,
            hidden_layers,
            output_dim,
            output_activation: Activation::Linear,
        }
    }

    pub fn layer_sizes(&self) -> Vec<usize> {
        let mut sizes = vec![self.input_dim];
        sizes.extend(self.hidden_layers.iter().map(|layer| layer.size));
        sizes.push(self.output_dim);
        sizes
    }
}

pub struct Layer {
    pub weights: Array2<f64>,
    pub bias: Array1<f64>,
    pub weights_grad: Array2<f64>,
    pub bias_grad: Array1<f64>,
    activation: Activation,
    residual: bool,
}

impl Layer {
    pub fn new(input_size: usize, spec: LayerSpec) -> Self {
        let mut rng = rand::thread_rng();
        let scale = match spec.activation {
            Activation::Relu => (2.0 / input_size.max(1) as f64).sqrt(),
            _ => (1.0 / input_size.max(1) as f64).sqrt(),
        };

        let weights = Array2::from_shape_fn((input_size.max(1), spec.size.max(1)), |_| {
            rng.gen_range(-scale..scale)
        });

        Self {
            weights,
            bias: Array1::zeros(spec.size.max(1)),
            weights_grad: Array2::zeros((input_size.max(1), spec.size.max(1))),
            bias_grad: Array1::zeros(spec.size.max(1)),
            activation: spec.activation,
            residual: spec.residual,
        }
    }

    fn forward_linear(&self, input: &Array1<f64>) -> Array1<f64> {
        input.dot(&self.weights) + &self.bias
    }

    fn can_apply_residual(&self, input_len: usize) -> bool {
        self.residual && input_len == self.bias.len()
    }
}

#[derive(Clone)]
struct LayerCache {
    input: Array1<f64>,
    pre_activation: Array1<f64>,
    residual_applied: bool,
}

pub struct Network {
    layers: Vec<Layer>,
    config: NetworkConfig,
    caches: Vec<LayerCache>,
}

impl Network {
    pub fn new(layer_sizes: Vec<usize>) -> Self {
        Self::from_config(NetworkConfig::from_layer_sizes(&layer_sizes))
    }

    pub fn from_config(config: NetworkConfig) -> Self {
        let mut layers = Vec::new();
        let mut previous_size = config.input_dim.max(1);

        for spec in &config.hidden_layers {
            let sanitized_spec = LayerSpec {
                size: spec.size.max(1),
                activation: spec.activation.clone(),
                residual: spec.residual,
            };
            layers.push(Layer::new(previous_size, sanitized_spec.clone()));
            previous_size = sanitized_spec.size;
        }

        layers.push(Layer::new(
            previous_size,
            LayerSpec {
                size: config.output_dim.max(1),
                activation: config.output_activation.clone(),
                residual: false,
            },
        ));

        Self {
            layers,
            config,
            caches: Vec::new(),
        }
    }

    pub fn infer(&self, input: &Array1<f64>) -> Array1<f64> {
        let mut output = input.clone();

        for layer in &self.layers {
            let pre_activation = layer.forward_linear(&output);
            let mut activated = layer.activation.apply(&pre_activation);
            if layer.can_apply_residual(output.len()) {
                activated = &activated + &output;
            }
            output = activated;
        }

        output
    }

    pub fn forward(&mut self, input: &Array1<f64>) -> Array1<f64> {
        self.caches.clear();
        let mut output = input.clone();

        for layer in &self.layers {
            let layer_input = output.clone();
            let pre_activation = layer.forward_linear(&layer_input);
            let mut activated = layer.activation.apply(&pre_activation);
            let residual_applied = layer.can_apply_residual(layer_input.len());

            if residual_applied {
                activated = &activated + &layer_input;
            }

            self.caches.push(LayerCache {
                input: layer_input,
                pre_activation,
                residual_applied,
            });

            output = activated;
        }

        output
    }

    pub fn backward(&mut self, grad_output: &Array1<f64>) {
        let mut grad = grad_output.clone();

        for index in (0..self.layers.len()).rev() {
            let cache = &self.caches[index];
            let layer = &mut self.layers[index];
            let activation_grad = layer.activation.derivative(&cache.pre_activation);
            let grad_pre = &grad * &activation_grad;

            for row in 0..layer.weights.nrows() {
                for col in 0..layer.weights.ncols() {
                    layer.weights_grad[[row, col]] += cache.input[row] * grad_pre[col];
                }
            }

            for col in 0..layer.bias.len() {
                layer.bias_grad[col] += grad_pre[col];
            }

            let mut grad_input = layer.weights.dot(&grad_pre);
            if cache.residual_applied {
                grad_input = &grad_input + &grad;
            }
            grad = grad_input;
        }
    }

    pub fn zero_grads(&mut self) {
        for layer in &mut self.layers {
            layer.weights_grad.fill(0.0);
            layer.bias_grad.fill(0.0);
        }
    }

    pub fn get_layers(&self) -> &Vec<Layer> {
        &self.layers
    }

    pub fn get_layers_mut(&mut self) -> &mut Vec<Layer> {
        &mut self.layers
    }

    pub fn config(&self) -> &NetworkConfig {
        &self.config
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum OptimizerKind {
    Adam,
    Sgd,
}

impl Default for OptimizerKind {
    fn default() -> Self {
        Self::Adam
    }
}

pub struct SGDOptimizer {
    learning_rate: f64,
}

impl SGDOptimizer {
    pub fn new(learning_rate: f64) -> Self {
        Self { learning_rate }
    }

    pub fn step(&mut self, network: &mut Network) {
        for layer in network.get_layers_mut() {
            for row in 0..layer.weights.nrows() {
                for col in 0..layer.weights.ncols() {
                    layer.weights[[row, col]] -= self.learning_rate * layer.weights_grad[[row, col]];
                }
            }

            for col in 0..layer.bias.len() {
                layer.bias[col] -= self.learning_rate * layer.bias_grad[col];
            }
        }
    }
}

pub struct AdamOptimizer {
    learning_rate: f64,
    beta1: f64,
    beta2: f64,
    epsilon: f64,
    t: usize,
    m_weights: Vec<Array2<f64>>,
    v_weights: Vec<Array2<f64>>,
    m_bias: Vec<Array1<f64>>,
    v_bias: Vec<Array1<f64>>,
}

impl AdamOptimizer {
    pub fn new(network: &Network, learning_rate: f64) -> Self {
        let mut m_weights = Vec::new();
        let mut v_weights = Vec::new();
        let mut m_bias = Vec::new();
        let mut v_bias = Vec::new();

        for layer in network.get_layers() {
            m_weights.push(Array2::zeros(layer.weights.dim()));
            v_weights.push(Array2::zeros(layer.weights.dim()));
            m_bias.push(Array1::zeros(layer.bias.len()));
            v_bias.push(Array1::zeros(layer.bias.len()));
        }

        Self {
            learning_rate,
            beta1: 0.9,
            beta2: 0.999,
            epsilon: 1e-8,
            t: 0,
            m_weights,
            v_weights,
            m_bias,
            v_bias,
        }
    }

    pub fn step(&mut self, network: &mut Network) {
        self.t += 1;

        let beta1_correction = 1.0 - self.beta1.powi(self.t as i32);
        let beta2_correction = 1.0 - self.beta2.powi(self.t as i32);
        let lr_t = self.learning_rate * beta2_correction.sqrt() / beta1_correction.max(1e-12);

        for (index, layer) in network.get_layers_mut().iter_mut().enumerate() {
            self.m_weights[index] =
                &self.m_weights[index] * self.beta1 + &layer.weights_grad * (1.0 - self.beta1);
            self.v_weights[index] = &self.v_weights[index] * self.beta2
                + &layer.weights_grad.mapv(|value| value * value) * (1.0 - self.beta2);

            for row in 0..layer.weights.nrows() {
                for col in 0..layer.weights.ncols() {
                    let moment = self.m_weights[index][[row, col]];
                    let velocity = self.v_weights[index][[row, col]];
                    layer.weights[[row, col]] -= lr_t * moment / (velocity.sqrt() + self.epsilon);
                }
            }

            self.m_bias[index] =
                &self.m_bias[index] * self.beta1 + &layer.bias_grad * (1.0 - self.beta1);
            self.v_bias[index] = &self.v_bias[index] * self.beta2
                + &layer.bias_grad.mapv(|value| value * value) * (1.0 - self.beta2);

            for col in 0..layer.bias.len() {
                let moment = self.m_bias[index][col];
                let velocity = self.v_bias[index][col];
                layer.bias[col] -= lr_t * moment / (velocity.sqrt() + self.epsilon);
            }
        }
    }
}

pub enum Optimizer {
    Adam(AdamOptimizer),
    Sgd(SGDOptimizer),
}

impl Optimizer {
    pub fn new(kind: OptimizerKind, network: &Network, learning_rate: f64) -> Self {
        match kind {
            OptimizerKind::Adam => Self::Adam(AdamOptimizer::new(network, learning_rate)),
            OptimizerKind::Sgd => Self::Sgd(SGDOptimizer::new(learning_rate)),
        }
    }

    pub fn step(&mut self, network: &mut Network) {
        match self {
            Optimizer::Adam(optimizer) => optimizer.step(network),
            Optimizer::Sgd(optimizer) => optimizer.step(network),
        }
    }
}
