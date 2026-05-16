import pandas as pd
import numpy as np

class LearningAnalytics:
    @staticmethod
    def get_score_level(score):
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "中等"
        elif score >= 60:
            return "及格"
        else:
            return "待提高"
    
    @staticmethod
    def calculate_total_score(eval_row, dimensions):
        scores = [eval_row.get(dim, 0) for dim in dimensions]
        return np.mean(scores) if scores else 0
    
    @staticmethod
    def identify_strength_weakness(student_df, dimensions):
        avg_scores = student_df[dimensions].mean()
        strengths = avg_scores[avg_scores >= 85].index.tolist()
        weaknesses = avg_scores[avg_scores < 70].index.tolist()
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "avg_by_dimension": avg_scores.to_dict()
        }
    
    @staticmethod
    def calculate_growth_rate(student_df, dimensions):
        if len(student_df) < 2:
            return 0
        first_avg = student_df.iloc[0][dimensions].mean()
        last_avg = student_df.iloc[-1][dimensions].mean()
        lessons_count = len(student_df)
        return round((last_avg - first_avg) / lessons_count, 2)
    
    @staticmethod
    def calculate_stability_index(student_df, dimensions):
        if len(student_df) < 2:
            return 100
        total_scores = student_df[dimensions].mean(axis=1)
        std = total_scores.std()
        return round(max(0, 100 - std * 10), 1)
    
    @staticmethod
    def generate_class_profile(class_df, dimensions):
        profile = {
            "total_students": class_df['student_id'].nunique(),
            "total_lessons": class_df['lesson_id'].nunique(),
            "avg_total_score": class_df[dimensions].mean(axis=1).mean(),
            "dimension_avgs": class_df[dimensions].mean().to_dict(),
            "score_distribution": class_df[dimensions].mean(axis=1).apply(
                lambda x: LearningAnalytics.get_score_level(x)
            ).value_counts().to_dict()
        }
        return profile
    
    @staticmethod
    def prepare_phase_summary(student_df, phase_name, dimensions):
        summary = {
            "phase_name": phase_name,
            "lessons_count": len(student_df),
            "date_range": f"{student_df['eval_date'].min()} 至 {student_df['eval_date'].max()}",
            "avg_scores_by_lesson": student_df.groupby('lesson_name')[dimensions].mean().to_dict(),
            "overall_avg": student_df[dimensions].mean().to_dict(),
            "growth_trend": LearningAnalytics.calculate_growth_rate(student_df, dimensions),
            "stability": LearningAnalytics.calculate_stability_index(student_df, dimensions),
            "strength_weakness": LearningAnalytics.identify_strength_weakness(student_df, dimensions)
        }
        return pd.DataFrame([summary])