// 测试行动选项解析逻辑 V2 - 适配新的格式
function testActionOptionsParsingV2() {
    console.log("============================================================");
    console.log("测试行动选项解析逻辑 V2 - 适配新的格式");
    console.log("============================================================");
    
    // 测试用例 - 包含新的格式
    const testCases = [
        {
            name: "新的格式（数字+中文冒号）",
            input: `<行动选项>
1：探索周围环境
2：与NPC对话
3：检查物品
</行动选项>`,
            expected: ["探索周围环境", "与NPC对话", "检查物品"]
        },
        {
            name: "英文冒号格式",
            input: `<行动选项>
1: 探索周围环境
2: 与NPC对话
3: 检查物品
</行动选项>`,
            expected: ["探索周围环境", "与NPC对话", "检查物品"]
        },
        {
            name: "顿号格式",
            input: `<行动选项>
1、探索周围环境
2、与NPC对话
3、检查物品
</行动选项>`,
            expected: ["探索周围环境", "与NPC对话", "检查物品"]
        },
        {
            name: "点号格式",
            input: `<行动选项>
1. 探索周围环境
2. 与NPC对话
3. 检查物品
</行动选项>`,
            expected: ["探索周围环境", "与NPC对话", "检查物品"]
        },
        {
            name: "混合格式",
            input: `<行动选项>
1：探索周围环境
2: 与NPC对话
3、检查物品
</行动选项>`,
            expected: ["探索周围环境", "与NPC对话", "检查物品"]
        },
        {
            name: "纯文本格式",
            input: `<行动选项>
探索周围环境
与NPC对话
检查物品
</行动选项>`,
            expected: ["探索周围环境", "与NPC对话", "检查物品"]
        },
        {
            name: "符号格式",
            input: `<行动选项>
- 探索周围环境
• 与NPC对话
* 检查物品
</行动选项>`,
            expected: ["探索周围环境", "与NPC对话", "检查物品"]
        },
        {
            name: "空行和空格处理",
            input: `<行动选项>

1：探索周围环境


2：与NPC对话

3：检查物品

</行动选项>`,
            expected: ["探索周围环境", "与NPC对话", "检查物品"]
        }
    ];
    
    // 使用新的解析逻辑
    function extractActionOptions(text) {
        if (!text) return [];
        
        const optionsStart = text.indexOf('<行动选项>');
        const optionsEnd = text.indexOf('</行动选项>');
        
        if (optionsStart === -1 || optionsEnd === -1) {
            return [];
        }
        
        const optionsText = text.substring(optionsStart + 6, optionsEnd);
        const options = [];
        
        // 增强兼容性：只要在<行动选项>标签内的每一行文字都当成一个行动进行渲染
        const lines = optionsText.split('\n');
        for (const line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine) {
                // 支持多种格式：
                // 1. 数字: 选项文本 (如 "1: 探索周围")
                // 2. 符号+选项文本 (如 "- 探索周围" 或 "• 探索周围")
                // 3. 纯文本选项 (如 "探索周围")
                
                let optionText = trimmedLine;
                
                // 移除常见的编号格式
                optionText = optionText
                    .replace(/^\d+[:：、.\s]+/, '')  // 移除数字+冒号(中英文)/顿号/点号
                    .replace(/^[-•*]\s*/, '')      // 移除符号+空格
                    .replace(/^【.*?】\s*/, '')     // 移除方括号内容
                    .replace(/^<.*?>\s*/, '')      // 移除HTML标签
                    .replace(/^[一二三四五六七八九十]+[、.\s]+/, '')  // 移除中文编号
                    .trim();
                
                // 如果移除格式后还有内容，则作为选项
                if (optionText) {
                    options.push(optionText);
                }
            }
        }
        
        return options;
    }
    
    // 运行测试
    let passed = 0;
    let failed = 0;
    
    testCases.forEach((testCase, index) => {
        console.log(`\n测试 ${index + 1}: ${testCase.name}`);
        console.log("-".repeat(40));
        
        const result = extractActionOptions(testCase.input);
        const expected = testCase.expected;
        
        console.log("输入:");
        console.log(testCase.input);
        console.log("\n期望结果:", expected);
        console.log("实际结果:", result);
        
        // 比较结果
        const isPass = JSON.stringify(result) === JSON.stringify(expected);
        
        if (isPass) {
            console.log("✅ 测试通过");
            passed++;
        } else {
            console.log("❌ 测试失败");
            failed++;
        }
    });
    
    console.log("\n============================================================");
    console.log(`测试总结: ${passed} 通过, ${failed} 失败`);
    console.log("============================================================");
    
    // 显示支持的格式示例
    console.log("\n📋 支持的格式示例:");
    console.log("-".repeat(40));
    console.log("1. 中文冒号: 1：探索周围");
    console.log("2. 英文冒号: 1: 探索周围");
    console.log("3. 顿号: 1、探索周围");
    console.log("4. 点号: 1. 探索周围");
    console.log("5. 符号: - 探索周围");
    console.log("6. 纯文本: 探索周围");
    console.log("7. 混合格式: 任意组合");
}

// 运行测试
testActionOptionsParsingV2();
