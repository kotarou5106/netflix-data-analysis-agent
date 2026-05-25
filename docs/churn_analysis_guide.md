# Churn Analysis Guide / 用户流失分析指南

This guide describes how churn analysis should be interpreted in this Netflix Data Analysis Agent project.

本文档说明 Netflix Data Analysis Agent 项目中用户流失分析的解释口径。

## How to Analyze User Churn / 如何分析用户流失

English: User churn analysis should compare churned and non-churned users across selected dimensions, then identify groups with relatively higher churn rates or weaker engagement signals.

中文：用户流失分析应比较流失用户与未流失用户在不同维度上的差异，并识别流失率相对更高或互动信号较弱的群体。

## Useful Analysis Dimensions / 可分析维度

English: Churn can be analyzed by subscription type, age, country or region, primary device, watch time, completion rate, recommendation click rate, account age, and recent login behavior.

中文：流失可以从订阅类型、年龄、国家或地区、主要设备、观看时长、完播率、推荐点击率、账号年龄和最近登录行为等维度进行分析。

## Correlation is not Causation / 相关性不等于因果性

English: Correlation is not Causation. If a group has a high churn rate, it means the group shows higher observed risk in this dataset. It does not directly prove that any single factor caused churn.

中文：相关性不等于因果性。如果某个群体流失率较高，只能说明该群体在本数据集中呈现更高的观察性风险，不能直接说明某个因素导致了流失。

## Interpreting High-Churn Groups / 如何解释高流失率群体

English: A high-churn group should be described as a higher-risk group. Recommendations should be framed as hypotheses for business testing, not as proven causal conclusions.

中文：高流失率群体应被描述为风险更高的群体。业务建议应表述为可进一步验证的业务假设，而不是已经被证明的因果结论。
