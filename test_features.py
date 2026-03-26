#!/usr/bin/env python3
"""
测试PINN-Solve v0.2.0新功能
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pinn-core/target/release'))

import numpy as np

def test_rust_module():
    """测试Rust模块导入和基本功能"""
    print("=" * 60)
    print("测试1: Rust模块导入")
    print("=" * 60)
    
    try:
        import pinn_core
        print("✅ Rust模块导入成功")
        
        # 测试网络创建
        solver = pinn_core.Solver([2, 16, 16, 1], 0.001)
        print("✅ 求解器创建成功")
        
        # 测试预测
        result = solver.predict([0.5, 0.5])
        print(f"✅ 单点预测成功: u(0.5, 0.5) = {result:.6f}")
        
        # 测试批量预测
        points = [[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]]
        results = solver.predict_batch(points)
        print(f"✅ 批量预测成功: {len(results)} 个点")
        
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_training():
    """测试训练功能"""
    print("\n" + "=" * 60)
    print("测试2: PDE求解器训练")
    print("=" * 60)
    
    try:
        import pinn_core
        
        # 创建求解器
        solver = pinn_core.Solver([2, 16, 16, 1], 0.01)
        print("✅ 求解器创建成功")
        
        # 生成训练数据
        n = 10
        x = np.linspace(0, 1, n)
        y = np.linspace(0, 1, n)
        X, Y = np.meshgrid(x, y)
        x_data = np.column_stack([X.ravel(), Y.ravel()]).tolist()
        print(f"✅ 生成 {len(x_data)} 个配点")
        
        # 训练
        print("🚀 开始训练...")
        losses = solver.train(x_data, epochs=100, n_boundary=40)
        print(f"✅ 训练完成")
        print(f"   初始损失: {losses[0]:.6f}")
        print(f"   最终损失: {losses[-1]:.6f}")
        print(f"   损失下降: {(1 - losses[-1]/losses[0])*100:.2f}%")
        
        # 测试解
        test_points = [
            [0.5, 0.5],
            [0.25, 0.25],
            [0.75, 0.75]
        ]
        print("\n📊 测试点预测:")
        for point in test_points:
            u = solver.predict(point)
            print(f"   u({point[0]}, {point[1]}) = {u:.6f}")
        
        return True
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api():
    """测试API接口"""
    print("\n" + "=" * 60)
    print("测试3: API接口")
    print("=" * 60)
    
    try:
        import requests
    except ImportError:
        print("⚠️  requests库未安装，跳过API测试")
        print("   安装: pip install requests")
        return False
    
    try:
        # 测试健康检查
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
        else:
            print("⚠️  后端服务未启动，跳过API测试")
            return False
        
        # 测试训练API
        config = {
            "layers": [2, 16, 16, 1],
            "learning_rate": 0.01,
            "epochs": 100,
            "n_points": 100,
            "n_boundary": 40
        }
        
        response = requests.post("http://localhost:8000/api/train/", json=config)
        if response.status_code == 200:
            task_id = response.json()["task_id"]
            print(f"✅ 训练任务创建成功: {task_id}")
            
            # 轮询状态
            status = None
            for _ in range(20):
                response = requests.get(f"http://localhost:8000/api/train/{task_id}/status", timeout=5)
                status = response.json()
                print(f"   当前状态: {status['status']}, progress = {status['progress']:.0%}")

                if status["status"] in {"completed", "failed", "cancelled"}:
                    break

                time.sleep(1)

            if not status or status["status"] != "completed":
                print(f"❌ 任务未成功完成: {status['status'] if status else 'unknown'}")
                return False

            print(f"✅ 状态查询成功: loss = {status['current_loss']:.6f}")
            
            # 获取解
            response = requests.get(f"http://localhost:8000/api/results/{task_id}")
            solution = response.json()["solution"]
            print(f"✅ 解获取成功: {len(solution['x'])}x{len(solution['y'])} 网格")
            
            return True
        else:
            print(f"❌ API调用失败: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  无法连接到后端服务，请先启动 API 和 Worker:")
        print("   cd backend && ./start-worker.sh")
        print("   cd backend && python main.py")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    print("\n" + "🎯" * 30)
    print("PINN-Solve v0.2.0 功能测试")
    print("🎯" * 30 + "\n")
    
    results = []
    
    # 测试1: Rust模块
    results.append(("Rust模块", test_rust_module()))
    
    # 测试2: 训练功能
    results.append(("训练功能", test_training()))
    
    # 测试3: API接口
    results.append(("API接口", test_api()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查错误信息")

if __name__ == "__main__":
    main()
