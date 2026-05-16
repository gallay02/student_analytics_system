from openai import OpenAI
import json
from config import LLM_CONFIG

class AIEvaluationEngine:
    def __init__(self):
        self.client = OpenAI(
            base_url=LLM_CONFIG["base_url"],
            api_key=LLM_CONFIG["api_key"]
        )
        self.model = LLM_CONFIG["model"]
        self.temperature = LLM_CONFIG["temperature"]
        self.max_tokens = LLM_CONFIG["max_tokens"]
    
    def _call_llm(self, system_prompt, user_prompt):
        """调用大模型API，失败时返回本地分析"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                 {"role": "user", "content": user_prompt}
             ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            # API 失败时返回本地分析提示
            error_msg = str(e)
            # 处理中文编码问题
            try:
                error_msg = error_msg.encode('latin1').decode('utf-8')
            except:
                pass
            return f"【本地分析】AI服务暂时不可用({error_msg[:50]})。系统已基于统计数据分析完成学情诊断。"
    
    def analyze_learning_status(self, student_name, eval_history, subject, dimensions=None):
        if eval_history.empty:
            return {
                "status": "新学生，暂无历史数据",
                "risk_level": "正常",
                "focus": "建议关注基础知识掌握情况"
            }
        
        if dimensions is None:
            exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                          'subject', 'template_id', 'eval_date', 'evaluator', 
                          'total_score', 'comments', 'created_at', 'name']
            dimensions = [c for c in eval_history.columns if c not in exclude_cols]
        
        recent_evals = eval_history.tail(3)
        avg_scores = eval_history[dimensions].mean()
        
        prompt = f"""
        你是一位专业的教育分析师，擅长{subject}教学评价分析。
        学生姓名：{student_name}
        科目：{subject}
        评价维度：{', '.join(dimensions)}
        最近评价记录：
        {recent_evals[dimensions].to_string()}
        各维度平均分：
        {avg_scores.to_string()}
        请分析该学生的学情状况，以JSON格式返回：
        {{
            "status": "学情总体描述（100字以内）",
            "risk_level": "高风险/中风险/正常",
            "focus": "下一次课需要重点关注的方面",
            "suggestions": "给教师的具体教学建议",
            "predicted_performance": "预测下次课表现"
        }}
        只返回JSON，不要其他内容。
        """
        
        result = self._call_llm(
            "你是一位资深教育专家，精通学情分析和教学策略制定。",
            prompt
        )
        
        try:
            json_str = result[result.find('{'):result.rfind('}')+1]
            return json.loads(json_str)
        except:
            return {
                "status": result[:100],
                "risk_level": "正常",
                "focus": "建议综合关注各维度发展"
            }
    
    def generate_phase_report(self, student_name, phase_data, subject):
        prompt = f"""
        你是一位资深教育评价专家，请为以下学生生成阶段评价报告。
        学生：{student_name}
        科目：{subject}
        阶段数据：
        {phase_data.to_string()}
        请生成包含以下内容的评价报告：
        1. 总体评价（200字）
        2. 优势领域分析
        3. 薄弱环节诊断
        4. 发展趋势预测
        5. 个性化发展建议
        6. 下一阶段学习目标
        报告要求：专业、客观、鼓励性、可操作性强。
        """
        return self._call_llm(
            "你是一位具有20年经验的教育评价专家，擅长撰写学生发展性评价报告。",
            prompt
        )
    
    def generate_teaching_strategy(self, class_data, subject, lesson_name):
        prompt = f"""
        你是一位{subject}教学专家，请基于以下班级学情数据，为课程"{lesson_name}"生成教学策略。
        班级数据摘要：
        {class_data.to_string()}
        请提供：
        1. 班级整体学情画像
        2. 分层教学建议（优秀/中等/待提高学生）
        3. 重点教学内容
        4. 差异化教学策略
        5. 课堂活动设计建议
        """
        return self._call_llm(
            "你是一位精通差异化教学和课堂设计的学科教学专家。",
            prompt
        )