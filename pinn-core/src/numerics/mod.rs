// 数值计算模块
use ndarray::Array2;

pub fn matrix_multiply(a: &Array2<f64>, b: &Array2<f64>) -> Array2<f64> {
    a.dot(b)
}
