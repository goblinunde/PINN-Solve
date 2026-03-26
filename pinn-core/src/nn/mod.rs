// 神经网络模块
use ndarray::{Array1, Array2};
use rand::Rng;

pub struct Layer {
    pub weights: Array2<f64>,
    pub bias: Array1<f64>,
    pub weights_grad: Array2<f64>,
    pub bias_grad: Array1<f64>,
}

impl Layer {
    pub fn new(input_size: usize, output_size: usize) -> Self {
        let mut rng = rand::thread_rng();
        let scale = (2.0 / input_size as f64).sqrt();
        
        let weights = Array2::from_shape_fn((input_size, output_size), |_| {
            rng.gen::<f64>() * scale - scale / 2.0
        });
        let bias = Array1::zeros(output_size);
        let weights_grad = Array2::zeros((input_size, output_size));
        let bias_grad = Array1::zeros(output_size);
        
        Self { weights, bias, weights_grad, bias_grad }
    }

    pub fn forward(&self, input: &Array1<f64>) -> Array1<f64> {
        input.dot(&self.weights) + &self.bias
    }

    pub fn backward(&mut self, input: &Array1<f64>, grad_output: &Array1<f64>) -> Array1<f64> {
        // 计算权重梯度: dL/dW = input^T * grad_output
        for i in 0..self.weights.nrows() {
            for j in 0..self.weights.ncols() {
                self.weights_grad[[i, j]] = input[i] * grad_output[j];
            }
        }
        
        // 计算偏置梯度
        self.bias_grad.assign(grad_output);
        
        // 计算输入梯度: dL/dinput = grad_output * W^T
        self.weights.t().dot(grad_output)
    }
}

#[derive(Clone)]
pub enum Activation {
    Tanh,
    Sigmoid,
    ReLU,
}

impl Activation {
    pub fn apply(&self, x: &Array1<f64>) -> Array1<f64> {
        match self {
            Activation::Tanh => x.mapv(|v| v.tanh()),
            Activation::Sigmoid => x.mapv(|v| 1.0 / (1.0 + (-v).exp())),
            Activation::ReLU => x.mapv(|v| v.max(0.0)),
        }
    }

    pub fn derivative(&self, x: &Array1<f64>) -> Array1<f64> {
        match self {
            Activation::Tanh => x.mapv(|v| {
                let t = v.tanh();
                1.0 - t * t
            }),
            Activation::Sigmoid => x.mapv(|v| {
                let s = 1.0 / (1.0 + (-v).exp());
                s * (1.0 - s)
            }),
            Activation::ReLU => x.mapv(|v| if v > 0.0 { 1.0 } else { 0.0 }),
        }
    }
}

pub struct Network {
    layers: Vec<Layer>,
    activation: Activation,
    // 缓存前向传播的中间结果
    layer_inputs: Vec<Array1<f64>>,
    layer_outputs: Vec<Array1<f64>>,
}

impl Network {
    pub fn new(layer_sizes: Vec<usize>) -> Self {
        let mut layers = Vec::new();
        for i in 0..layer_sizes.len() - 1 {
            layers.push(Layer::new(layer_sizes[i], layer_sizes[i + 1]));
        }
        Self {
            layers,
            activation: Activation::Tanh,
            layer_inputs: Vec::new(),
            layer_outputs: Vec::new(),
        }
    }

    pub fn forward(&mut self, input: &Array1<f64>) -> Array1<f64> {
        self.layer_inputs.clear();
        self.layer_outputs.clear();
        
        let mut output = input.clone();
        self.layer_inputs.push(output.clone());
        
        for (i, layer) in self.layers.iter().enumerate() {
            output = layer.forward(&output);
            self.layer_outputs.push(output.clone());
            
            if i < self.layers.len() - 1 {
                output = self.activation.apply(&output);
                self.layer_inputs.push(output.clone());
            }
        }
        output
    }

    pub fn backward(&mut self, grad_output: &Array1<f64>) {
        let mut grad = grad_output.clone();
        
        for i in (0..self.layers.len()).rev() {
            let input = &self.layer_inputs[i];
            
            // 如果不是最后一层，需要乘以激活函数的导数
            if i < self.layers.len() - 1 {
                let layer_output = &self.layer_outputs[i];
                let activation_grad = self.activation.derivative(layer_output);
                grad = &grad * &activation_grad;
            }
            
            grad = self.layers[i].backward(input, &grad);
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
}

/// Adam优化器
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
        let lr_t = self.learning_rate * ((1.0 - self.beta2.powi(self.t as i32)).sqrt())
            / (1.0 - self.beta1.powi(self.t as i32));
        
        for (i, layer) in network.get_layers_mut().iter_mut().enumerate() {
            // 更新权重
            self.m_weights[i] = &self.m_weights[i] * self.beta1 + &layer.weights_grad * (1.0 - self.beta1);
            self.v_weights[i] = &self.v_weights[i] * self.beta2 + &layer.weights_grad.mapv(|x| x * x) * (1.0 - self.beta2);
            
            let m_hat = &self.m_weights[i];
            let v_hat = &self.v_weights[i];
            
            for ((w, m), v) in layer.weights.iter_mut().zip(m_hat.iter()).zip(v_hat.iter()) {
                *w -= lr_t * m / (v.sqrt() + self.epsilon);
            }
            
            // 更新偏置
            self.m_bias[i] = &self.m_bias[i] * self.beta1 + &layer.bias_grad * (1.0 - self.beta1);
            self.v_bias[i] = &self.v_bias[i] * self.beta2 + &layer.bias_grad.mapv(|x| x * x) * (1.0 - self.beta2);
            
            for j in 0..layer.bias.len() {
                layer.bias[j] -= lr_t * self.m_bias[i][j] / (self.v_bias[i][j].sqrt() + self.epsilon);
            }
        }
    }
}
