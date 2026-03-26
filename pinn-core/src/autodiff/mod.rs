// 自动微分模块
use ndarray::{Array1, Array2};

/// 计算数值梯度（用于验证）
pub fn numerical_gradient<F>(f: F, x: &Array1<f64>, epsilon: f64) -> Array1<f64>
where
    F: Fn(&Array1<f64>) -> f64,
{
    let mut grad = Array1::zeros(x.len());
    for i in 0..x.len() {
        let mut x_plus = x.clone();
        let mut x_minus = x.clone();
        x_plus[i] += epsilon;
        x_minus[i] -= epsilon;
        grad[i] = (f(&x_plus) - f(&x_minus)) / (2.0 * epsilon);
    }
    grad
}

/// 计算激活函数的导数
pub fn tanh_derivative(x: f64) -> f64 {
    let t = x.tanh();
    1.0 - t * t
}

pub fn sigmoid_derivative(x: f64) -> f64 {
    let s = 1.0 / (1.0 + (-x).exp());
    s * (1.0 - s)
}

pub fn relu_derivative(x: f64) -> f64 {
    if x > 0.0 { 1.0 } else { 0.0 }
}

/// 计算偏导数（用于PDE残差）
pub fn compute_derivative(
    network_output: &dyn Fn(&Array1<f64>) -> f64,
    x: &Array1<f64>,
    var_index: usize,
    epsilon: f64,
) -> f64 {
    let mut x_plus = x.clone();
    let mut x_minus = x.clone();
    x_plus[var_index] += epsilon;
    x_minus[var_index] -= epsilon;
    (network_output(&x_plus) - network_output(&x_minus)) / (2.0 * epsilon)
}

/// 计算二阶偏导数
pub fn compute_second_derivative(
    network_output: &dyn Fn(&Array1<f64>) -> f64,
    x: &Array1<f64>,
    var_index: usize,
    epsilon: f64,
) -> f64 {
    let mut x_plus = x.clone();
    let mut x_minus = x.clone();
    x_plus[var_index] += epsilon;
    x_minus[var_index] -= epsilon;
    
    let f_plus = network_output(&x_plus);
    let f_center = network_output(x);
    let f_minus = network_output(&x_minus);
    
    (f_plus - 2.0 * f_center + f_minus) / (epsilon * epsilon)
}
