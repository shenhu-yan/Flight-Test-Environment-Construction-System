"""
飞行试验环境 - 示例训练脚本
此脚本演示如何使用生成的环境进行训练，并通过WebSocket上报指标
"""

import time
import json
import random
import asyncio
import websockets

# 配置
API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/metrics"
TOKEN = None  # 需要从登录接口获取
PROJECT_ID = None  # 需要从项目列表获取
ENV_ID = None  # 需要从环境列表获取


def simulate_training_step(step: int) -> dict:
    """模拟训练步骤，返回指标"""
    # 模拟训练指标
    episode_reward = 100 + step * 0.5 + random.uniform(-10, 10)
    success_rate = min(0.3 + step * 0.01 + random.uniform(-0.05, 0.05), 1.0)
    convergence_speed = min(0.2 + step * 0.005 + random.uniform(-0.02, 0.02), 1.0)

    return {
        "episode_reward": round(episode_reward, 2),
        "success_rate": round(success_rate, 4),
        "convergence_speed": round(convergence_speed, 4),
        "step": step
    }


async def report_metrics(token: str, project_id: str, env_id: str, metrics: dict):
    """通过WebSocket上报训练指标"""
    try:
        async with websockets.connect(f"{WS_URL}?token={token}") as ws:
            message = {
                "type": "metric_report",
                "project_id": project_id,
                "env_id": env_id,
                "task_id": "example_task",
                "timestamp": int(time.time()),
                "metrics": metrics
            }
            await ws.send(json.dumps(message))
            print(f"  上报指标: step={metrics['step']}, reward={metrics['episode_reward']:.2f}")

            # 等待服务器响应
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            except asyncio.TimeoutError:
                pass

    except Exception as e:
        print(f"  WebSocket连接失败: {e}")
        print("  (这在本地训练时是正常的，服务器会接收指标)")


def simple_training_loop():
    """简单的训练循环示例"""
    print("=" * 60)
    print("飞行试验环境 - 简单训练示例")
    print("=" * 60)
    print()
    print("注意：此示例模拟训练过程。")
    print("实际训练需要：")
    print("1. 从系统下载环境包")
    print("2. 安装依赖: pip install gymnasium numpy")
    print("3. 导入并使用 FlightEnv 类")
    print()
    print("=" * 60)
    print()

    # 模拟训练参数
    total_steps = 100
    report_interval = 10

    print(f"开始模拟训练，共 {total_steps} 步...")
    print()

    for step in range(1, total_steps + 1):
        # 模拟训练步骤
        metrics = simulate_training_step(step)

        # 每隔一定步数打印进度
        if step % report_interval == 0:
            print(f"[Step {step}/{total_steps}]")
            print(f"  奖励值: {metrics['episode_reward']:.2f}")
            print(f"  成功率: {metrics['success_rate']:.4f}")
            print(f"  收敛速度: {metrics['convergence_speed']:.4f}")
            print()

        # 模拟训练延迟
        time.sleep(0.1)

    print("=" * 60)
    print("模拟训练完成！")
    print()
    print("实际使用方法：")
    print("1. 在Web界面创建项目和环境")
    print("2. 下载环境包 (GET /api/envs/{env_id}/export)")
    print("3. 解压并导入环境")
    print("4. 使用下面的代码进行训练：")
    print()
    print("```python")
    print("import gymnasium as gym")
    print("from env.core import FlightEnv")
    print("")
    print("# 创建环境")
    print("env = FlightEnv('config.json')")
    print("")
    print("# 训练循环")
    print("obs, info = env.reset()")
    print("for step in range(1000):")
    print("    action = env.action_space.sample()  # 随机动作")
    print("    obs, reward, terminated, truncated, info = env.step(action)")
    print("    if terminated or truncated:")
    print("        obs, info = env.reset()")
    print("env.close()")
    print("```")
    print()


def main():
    """主函数"""
    print("飞行试验环境构建系统 - 训练示例")
    print()
    print("系统功能说明：")
    print("1. 登录系统 (admin/admin123)")
    print("2. 创建项目")
    print("3. 选择模板或自定义配置")
    print("4. 生成环境")
    print("5. 下载环境包到本地")
    print("6. 在本地执行RL训练")
    print("7. 训练指标通过WebSocket实时上报")
    print("8. 在Web界面监控训练过程")
    print("9. 根据训练情况调整环境参数")
    print("10. 使用智能优化功能优化环境")
    print()

    choice = input("选择操作：\n1. 运行模拟训练示例\n2. 查看API使用说明\n请输入选项 (1/2): ")

    if choice == "1":
        simple_training_loop()
    elif choice == "2":
        print_api_usage()
    else:
        print("无效选项")


def print_api_usage():
    """打印API使用说明"""
    print()
    print("=" * 60)
    print("API 使用说明")
    print("=" * 60)
    print()
    print("1. 登录获取Token:")
    print('   curl -X POST http://localhost:8000/api/auth/login \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"username":"admin","password":"admin123"}\'')
    print()
    print("2. 创建项目:")
    print('   curl -X POST http://localhost:8000/api/projects \\')
    print('     -H "Authorization: Bearer <token>" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"name":"我的项目"}\'')
    print()
    print("3. 获取模板列表:")
    print('   curl http://localhost:8000/api/templates \\')
    print('     -H "Authorization: Bearer <token>"')
    print()
    print("4. 创建环境:")
    print('   curl -X POST http://localhost:8000/api/envs \\')
    print('     -H "Authorization: Bearer <token>" \\')
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"project_id":"<id>","name":"我的环境","config":{...}}\'')
    print()
    print("5. 下载环境包:")
    print('   curl -O http://localhost:8000/api/envs/<env_id>/export \\')
    print('     -H "Authorization: Bearer <token>"')
    print()
    print("6. WebSocket上报指标:")
    print('   ws://localhost:8000/ws/metrics?token=<token>')
    print()
    print("完整API文档: http://localhost:8000/docs")
    print()


if __name__ == "__main__":
    main()
