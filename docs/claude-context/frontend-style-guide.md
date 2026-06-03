---
name: frontend-style-guide
description: 前端视觉设计规范V1，黑白灰质感风格，用于QuantEvo重构
metadata: 
  node_type: memory
  type: project
  originSessionId: 61e9a59f-cef2-41bb-a951-ddf0d0e98814
---

# 前端视觉设计规范 V1

## 一、设计理念

**方向**: 现代量化终端 × 消费级App质感  
**关键词**: 克制、精确、有温度、有分量  
**参考**: Linear / Craft / Apple Design / 现代量化终端

## 二、色彩系统

```
主色调（黑白灰）:
--black:     #171717  (主色，按钮、标题、品牌)
--gray-800:  #262626  (hover态)
--gray-700:  #404040  (次级强调)
--gray-600:  #525252  (正文)
--gray-500:  #737373  (次要文字)
--gray-400:  #a3a3a3  (占位符)
--gray-300:  #d4d4d4  (禁用、分割线)
--gray-200:  #e5e5e5  (边框)
--gray-100:  #f5f5f5  (次级背景)
--white:     #ffffff  (卡片)
--bg:        #fafafa  (页面背景)

点缀色（极少使用）:
--green:     #22c55e  (健康、在线、上涨)
--red:       #ef4444  (告警、下跌)
--amber:     #d97706  (寿命预警)
```

## 三、纹理系统

三层叠加，全部 `pointer-events: none`:

1. **噪点纹理** (opacity: 0.035)
   - SVG fractalNoise, baseFrequency=0.9
   - background-size: 128px 128px

2. **网格纹理** (opacity: 0.028)
   - linear-gradient 横竖线，48px间隔
   - mask: 上下渐变淡出

3. **聚光灯光晕**
   - radial-gradient 顶部 + 右侧两个光斑
   - 给页面增加空间感

## 四、字体

```css
font-family: 'Inter', 'SF Pro Display', 'PingFang SC', 'Microsoft YaHei', -apple-system, sans-serif;
```

层级:
| 层级 | 大小 | 字重 | 字间距 | 颜色 |
|------|------|------|--------|------|
| 大标题 | 2rem-2.6rem | 800 | -0.04em | #171717 |
| 标题 | 1.4rem-1.8rem | 700 | -0.03em | #171717 |
| 正文 | 0.88rem | 500 | -0.01em | #525252 |
| 标签 | 0.62rem | 700 | 0.1em | #d4d4d4 |
| 数据 | 1.4rem-1.8rem | 700 | -0.02em | #171717 |

## 五、卡片

```css
border-radius: 16px-20px;
background: #fff;
border: 1px solid rgba(0,0,0,0.05-0.06);
box-shadow:
  0 1px 2px rgba(0,0,0,0.02),
  0 4px 16px rgba(0,0,0,0.03);

/* hover */
transform: translateY(-1px);
box-shadow: 0 12px 32px rgba(0,0,0,0.06);
border-color: rgba(0,0,0,0.08);

/* 顶部光泽线 */
::before {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.04), transparent);
}

/* hover光晕 */
.card-glow {
  radial-gradient(circle, rgba(0,0,0,0.025) 0%, transparent 70%);
}
```

## 六、按钮

主按钮:
```css
background: #171717;
color: #fff;
border-radius: 16px;
padding: 17px 24px;
font-weight: 600;
letter-spacing: -0.01em;
box-shadow: 0 4px 16px rgba(0,0,0,0.12);

/* 扫光动画 */
::before {
  left: -100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
  transition: left 0.5s;
}
:hover::before { left: 100%; }
```

## 七、过渡动画

```css
transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
```

## 八、底部Tab Bar

```css
background: rgba(255,255,255,0.92);
backdrop-filter: blur(20px) saturate(1.3);
border-top: 1px solid rgba(0,0,0,0.05);
padding-bottom: env(safe-area-inset-bottom);

/* active */
color: #171717;
::before { /* 顶部指示条 */
  width: 20px; height: 3px;
  background: #171717;
  border-radius: 0 0 3px 3px;
}
```

## 九、响应式

桌面端 (>768px):
- 内容区 max-width: 720px, 居中
- Tab bar 浮动居中，底部有间距，圆角顶部
- 特征卡片横向排列
- 操作按钮 4列

## 十、组件清单

| 组件 | 位置 |
|------|------|
| 顶部导航栏 | App.vue / DemoView.vue |
| 底部Tab Bar | App.vue / DemoView.vue |
| 卡片容器 | Card.vue |
| 主按钮 | Button.vue |
| 标签 | Tag.vue |
| 数据展示 | Stat.vue |
| 环形图 | DonutChart.vue |
| 折线图 | LineChart.vue |
| 告警条 | AlertBar.vue |
| 步骤指示器 | StepIndicator.vue |
| 问卷选项 | OptionCard.vue |
