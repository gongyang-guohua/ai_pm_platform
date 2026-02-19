import json
import asyncio
from typing import List, Dict, Any
from app.core.llm import llm_service

class DeepFlowAgent:
    def __init__(self):
        pass

    async def run_analysis(self, project_data: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """
        Agent 1: Data Analyst
        Analyzes quantitative metrics, schedule performance, and variance.
        """
        if language == "zh":
            prompt = f"""
            你是一位专家项目数据分析师。分析以下项目数据并提取关键绩效指标。
            
            项目: {project_data.get('title')}
            任务数: {len(project_data.get('tasks', []))}
            
            数据:
            {json.dumps(project_data.get('stats', {}), indent=2)}
            
            任务状态分布:
            {json.dumps(project_data.get('status_distribution', {}), indent=2)}
            
            识别:
            1. CPI/SPI 趋势 (如果有)
            2. 进度偏差分析
            3. 基于当前速度的完工预测
            
            仅输出有效的JSON:
            {{
                "health_score": <0-100>,
                "schedule_status": "ahead" | "on_track" | "behind",
                "key_metrics": {{ ... }},
                "analysis_summary": "..."
            }}
            """
        else:
            prompt = f"""
            You are an Expert Project Data Analyst. Analyze the following project data and extract key performance metrics.
            
            Project: {project_data.get('title')}
            Tasks: {len(project_data.get('tasks', []))}
            
            Data:
            {json.dumps(project_data.get('stats', {}), indent=2)}
            
            Task Status Distribution:
            {json.dumps(project_data.get('status_distribution', {}), indent=2)}
            
            Identify:
            1. CPI/SPI trends (if available)
            2. Schedule Variance analysis
            3. Completion forecast based on current velocity
            
            Output valid JSON only:
            {{
                "health_score": <0-100>,
                "schedule_status": "ahead" | "on_track" | "behind",
                "key_metrics": {{ ... }},
                "analysis_summary": "..."
            }}
            """
        response = await llm_service.generate_json(prompt)
        return response

    async def run_risk_assessment(self, project_data: Dict[str, Any], analysis_result: Dict[str, Any], language: str = "en") -> Dict[str, Any]:
        """
        Agent 2: Risk Manager
        Identifies potential risks, logical fallacies in schedule, and bottlenecks.
        """
        tasks = project_data.get('tasks', [])
        # Simplify tasks for prompt context
        task_summary = [
            f"- {t.get('title')} ({t.get('status')}, Est: {t.get('original_duration')}h, Float: {t.get('total_float')}h)"
            for t in tasks[:50] # Limit context
        ]
        
        if language == "zh":
            prompt = f"""
            你是一位高级风险经理，专注于建筑/工程项目。
            审查分析师的发现和任务列表以识别风险。
            
            分析师报告:
            {json.dumps(analysis_result)}
            
            任务样本:
            {chr(10).join(task_summary)}
            
            识别:
            1. 关键路径风险 (低浮动时间任务)
            2. 资源瓶颈 (连续的繁重任务)
            3. 逻辑缺口
            
            仅输出有效的JSON:
            {{
                "risk_level": "low" | "medium" | "high",
                "top_risks": [
                    {{ "risk": "...", "impact": "...", "mitigation": "..." }}
                ],
                "bottlenecks": [...]
            }}
            """
        else:
            prompt = f"""
            You are a Senior Risk Manager. specific focus on construction/engineering projects.
            Review the Analyst's findings and the task list to identify risks.
            
            Analyst Report:
            {json.dumps(analysis_result)}
            
            Task Sample:
            {chr(10).join(task_summary)}
            
            Identify:
            1. Critical Path risks (Low float tasks)
            2. Resource bottlenecks (consecutive heavy tasks)
            3. Logical gaps
            
            Output valid JSON only:
            {{
                "risk_level": "low" | "medium" | "high",
                "top_risks": [
                    {{ "risk": "...", "impact": "...", "mitigation": "..." }}
                ],
                "bottlenecks": [...]
            }}
            """
        response = await llm_service.generate_json(prompt)
        return response

    async def write_report(self, project_data: Dict[str, Any], analysis: Dict[str, Any], risks: Dict[str, Any], report_type: str, language: str = "en") -> str:
        """
        Agent 3: Executive Writer
        Synthesizes all intelligence into a final formatted report.
        """
        if language == "zh":
            prompt = f"""
            你是一个高管报告引擎。撰写一份专业的{report_type}报告 (中文)。
            
            项目: {project_data.get('title')}
            描述: {project_data.get('description')}
            
            [数据分析]
            {json.dumps(analysis, indent=2)}
            
            [风险评估]
            {json.dumps(risks, indent=2)}
            
            格式: Markdown. 
            风格: 专业、简洁、以行动为导向。像彭博终端备忘录一样。
            
            章节:
            # 执行摘要
            # 进度绩效 (包括CPI/SPI分析)
            # 关键风险与缓解措施
            # 下一阶段的战略建议
            """
        else:
            prompt = f"""
            You are an Executive Reporting engine. Write a professional {report_type} report.
            
            Project: {project_data.get('title')}
            Description: {project_data.get('description')}
            
            [Data Analysis]
            {json.dumps(analysis, indent=2)}
            
            [Risk Assessment]
            {json.dumps(risks, indent=2)}
            
            Format: Markdown. 
            Style: Professional, concise, action-oriented. Like a Bloomberg Terminal memo.
            
            Sections:
            # Executive Summary
            # Schedule Performance (Include CPI/SPI analysis)
            # Critical Risks & Mitigation
            # Strategic Recommendations for Next Cycle
            """
        return await llm_service.generate_text(prompt)

    async def generate_deepflow_report(self, project: Any, report_type: str = "weekly", language: str = "en") -> str:
        # 1. Prepare Data
        tasks_data = [
            {
                "title": t.title,
                "status": t.status,
                "original_duration": t.original_duration,
                "total_float": t.total_float,
                "planned_end": str(t.planned_end) if t.planned_end else None
            }
            for t in project.tasks
        ]
        
        # Calculate basic stats distribution
        status_dist = {}
        for t in project.tasks:
            status_dist[t.status] = status_dist.get(t.status, 0) + 1
            
        project_context = {
            "title": project.title,
            "description": project.description,
            "tasks": tasks_data,
            "status_distribution": status_dist,
            # Placeholder for calculated EVM stats if they existed on model
            "stats": {
                "cpi": 1.0, # Mock or retrieve real calculation
                "spi": 1.0
            }
        }

        # 2. Multi-Agent Workflow
        try:
            # Parallel or Sequential - Sequential for dependent context
            analysis = await self.run_analysis(project_context, language)
            risks = await self.run_risk_assessment(project_context, analysis, language)
            final_report = await self.write_report(project_context, analysis, risks, report_type, language)
            
            return final_report
        except Exception as e:
            print(f"DeepFlow Error: {e}")
            # Fallback
            msg = f"生成 DeepFlow 报告时出错: {str(e)}" if language == "zh" else f"Error generating DeepFlow report: {str(e)}"
            return msg

deepflow_agent = DeepFlowAgent()
