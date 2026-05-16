from ai_engine import AIEvaluationEngine
from analytics import LearningAnalytics

class ReportGenerator:
    def __init__(self):
        self.ai = AIEvaluationEngine()
        self.analytics = LearningAnalytics()
    
    def generate_pre_lesson_report(self, student_id, student_name, subject, next_lesson, dimensions=None, template_id=None):
        from database import get_student_evaluations
        import json
        
        eval_history = get_student_evaluations(student_id, subject)
        
        if dimensions is None and not eval_history.empty:
            exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                          'subject', 'template_id', 'eval_date', 'evaluator', 
                          'total_score', 'comments', 'created_at', 'name']
            dimensions = [c for c in eval_history.columns if c not in exclude_cols]
        elif dimensions is None:
            dimensions = []
        
        ai_result = self.ai.analyze_learning_status(student_name, eval_history, subject, dimensions)
        
        if not eval_history.empty and dimensions:
            growth = self.analytics.calculate_growth_rate(eval_history, dimensions)
            stability = self.analytics.calculate_stability_index(eval_history, dimensions)
            sw = self.analytics.identify_strength_weakness(eval_history, dimensions)
        else:
            growth = 0
            stability = 100
            sw = {"strengths": [], "weaknesses": [], "avg_by_dimension": {}}
        
        report = {
            "student_name": student_name,
            "subject": subject,
            "next_lesson": next_lesson,
            "ai_analysis": ai_result,
            "statistics": {
                "total_lessons": len(eval_history),
                "growth_rate": growth,
                "stability_index": stability,
                "strengths": sw["strengths"],
                "weaknesses": sw["weaknesses"]
            },
            "dimension_scores": sw.get("avg_by_dimension", {})
        }
        
        from database import save_learning_status
        save_learning_status({
            "student_id": student_id,
            "lesson_id": next_lesson,
            "subject": subject,
            "pre_lesson_status": json.dumps(report, ensure_ascii=False),
            "risk_level": ai_result.get("risk_level", "正常"),
            "suggested_focus": ai_result.get("focus", "")
        })
        
        return report
    
    def generate_phase_evaluation(self, student_id, student_name, subject, phase_name, start_date, end_date, dimensions=None):
        from database import get_student_evaluations
        import pandas as pd
        
        eval_history = get_student_evaluations(student_id, subject)
        eval_history = eval_history[
            (eval_history['eval_date'] >= start_date) & 
            (eval_history['eval_date'] <= end_date)
        ]
        
        if eval_history.empty:
            return None
        
        if dimensions is None:
            exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                          'subject', 'template_id', 'eval_date', 'evaluator', 
                          'total_score', 'comments', 'created_at', 'name']
            dimensions = [c for c in eval_history.columns if c not in exclude_cols]
        
        overall_score = eval_history[dimensions].mean().mean()
        level = self.analytics.get_score_level(overall_score)
        sw = self.analytics.identify_strength_weakness(eval_history, dimensions)
        growth = self.analytics.calculate_growth_rate(eval_history, dimensions)
        
        phase_data = self.analytics.prepare_phase_summary(eval_history, phase_name, dimensions)
        ai_report = self.ai.generate_phase_report(student_name, phase_data, subject)
        
        phase_eval = {
            "student_id": student_id,
            "subject": subject,
            "phase_name": phase_name,
            "start_date": start_date,
            "end_date": end_date,
            "overall_score": round(overall_score, 2),
            "overall_level": level,
            "strength_areas": ", ".join(sw["strengths"]),
            "weakness_areas": ", ".join(sw["weaknesses"]),
            "development_suggestions": f"进步率: {growth}/课时",
            "ai_report": ai_report
        }
        
        from database import save_phase_evaluation
        save_phase_evaluation(phase_eval)
        
        return phase_eval
    
    def generate_class_strategy(self, lesson_id, subject, lesson_name, dimensions=None):
        from database import get_class_evaluations
        import pandas as pd
        
        class_data = get_class_evaluations(lesson_id, subject)
        if class_data.empty:
            return None
        
        if dimensions is None:
            exclude_cols = ['eval_id', 'student_id', 'lesson_id', 'lesson_name', 
                          'subject', 'template_id', 'eval_date', 'evaluator', 
                          'total_score', 'comments', 'created_at', 'name']
            dimensions = [c for c in class_data.columns if c not in exclude_cols]
        
        summary = class_data[dimensions].describe()
        strategy = self.ai.generate_teaching_strategy(summary, subject, lesson_name)
        
        return {
            "lesson_name": lesson_name,
            "class_size": class_data['student_id'].nunique(),
            "statistics": summary.to_dict(),
            "strategy": strategy
        }