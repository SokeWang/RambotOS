"""
简单的集成测试脚本，验证中间件功能
"""
import asyncio
from langchain_agent import UltronBrain


async def test_middleware_integration():
    """测试中间件集成"""
    print("🧪 开始测试中间件集成...")
    
    try:
        # 1. 初始化 UltronBrain
        print("\n1️⃣ 初始化 UltronBrain...")
        brain = UltronBrain()
        await brain.initialize()
        print("   ✅ 初始化成功")
        
        # 2. 验证中间件已创建
        print("\n2️⃣ 验证中间件...")
        assert brain.tool_selector_middleware is not None, "中间件未创建"
        print(f"   ✅ 中间件已创建: {type(brain.tool_selector_middleware).__name__}")
        
        # 3. 验证 BrainAgent 有 agent 实例
        print("\n3️⃣ 验证 BrainAgent...")
        assert brain.brain_manager is not None, "BrainAgent 未创建"
        assert hasattr(brain.brain_manager, 'agent'), "BrainAgent 没有 agent 属性"
        print(f"   ✅ BrainAgent 已创建，包含 {len(brain.brain_manager.tools)} 个工具")
        
        # 4. 验证工具检索器已索引
        print("\n4️⃣ 验证工具索引...")
        if brain.all_mcp_tools:
            print(f"   ✅ 已索引 {len(brain.all_mcp_tools)} 个 MCP 工具")
        else:
            print("   ⚠️  没有可用的 MCP 工具（这可能是正常的）")
        
        # 5. 测试简单查询（不实际调用 LLM）
        print("\n5️⃣ 测试中间件工具选择逻辑...")
        test_query = "帮我计算 2 + 2"
        retrieved = brain.tool_selector_middleware._retrieve_tools(
            test_query, 
            brain.brain_manager.tools
        )
        print(f"   ✅ 查询: '{test_query}'")
        print(f"   ✅ 选择的工具: {retrieved}")
        
        print("\n" + "="*60)
        print("✅ 所有测试通过！中间件集成成功！")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_middleware_integration())
    exit(0 if success else 1)
