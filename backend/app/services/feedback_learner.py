from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlmodel import Session, select

from app.models.feedback import BidRecord, FeedbackAnalysis


class FeedbackLearner:
    """反馈学习系统
    
    记录投标行为和结果，分析预测准确性，触发模型优化
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def record_bid(
        self, 
        tender_id: int, 
        bid_info: Dict[str, Any], 
        prediction: Dict[str, Any]
    ) -> BidRecord:
        """记录投标行为
        
        Args:
            tender_id: 招标项目ID
            bid_info: 投标信息（bid_date, bid_price等）
            prediction: 系统预测结果（score, recommendation, grade）
        
        Returns:
            BidRecord: 创建的投标记录
        """
        record = BidRecord(
            tender_id=tender_id,
            bid_date=bid_info.get('bid_date', datetime.now()),
            bid_price=bid_info.get('bid_price', 0),
            predicted_score=prediction.get('score', 0),
            predicted_recommendation=prediction.get('recommendation', ''),
            predicted_grade=prediction.get('grade', 'D'),
            actual_result='待定'
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        return record
    
    def record_result(
        self, 
        record_id: int, 
        result: Dict[str, Any]
    ) -> Optional[BidRecord]:
        """记录投标结果
        
        Args:
            record_id: 投标记录ID
            result: 结果信息（is_won, win_date, lose_reason, notes）
        
        Returns:
            BidRecord: 更新后的投标记录
        """
        record = self.db.get(BidRecord, record_id)
        if not record:
            return None
        
        record.is_won = result.get('is_won', False)
        record.win_date = result.get('win_date')
        record.lose_reason = result.get('lose_reason')
        record.feedback_notes = result.get('notes')
        record.actual_result = '中标' if record.is_won else '未中标'
        record.updated_at = datetime.now()
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        self._trigger_optimization(record)
        
        return record
    
    def _trigger_optimization(self, record: BidRecord):
        """触发模型优化分析"""
        if record.is_won and record.predicted_score < 60:
            print(f"[优化提示] 低分预测但中标: 项目ID={record.tender_id}, "
                  f"预测分={record.predicted_score}, 建议优化评分模型")
        
        if not record.is_won and record.predicted_score >= 80:
            print(f"[优化提示] 高分预测但未中标: 项目ID={record.tender_id}, "
                  f"预测分={record.predicted_score}, 原因={record.lose_reason}")
            
            if record.lose_reason:
                self._analyze_failure_pattern(record)
    
    def _analyze_failure_pattern(self, record: BidRecord):
        """分析失败模式"""
        reason = record.lose_reason or ""
        
        if '价格' in reason or '报价' in reason:
            print("  -> 建议优化报价策略")
        elif '资质' in reason:
            print("  -> 建议补充资质")
        elif '技术' in reason:
            print("  -> 建议提升技术方案质量")
    
    def get_accuracy_stats(self) -> Dict[str, Any]:
        """获取预测准确性统计"""
        statement = select(BidRecord).where(BidRecord.actual_result != '待定')
        records = self.db.exec(statement).all()
        
        if not records:
            return {
                'total': 0,
                'accuracy': 0,
                'message': '暂无已完成的投标记录'
            }
        
        total = len(records)
        correct = 0
        
        high_threshold = 60
        
        for record in records:
            if record.is_won and record.predicted_score >= high_threshold:
                correct += 1
            elif not record.is_won and record.predicted_score < high_threshold:
                correct += 1
        
        accuracy = correct / total if total > 0 else 0
        
        return {
            'total': total,
            'correct': correct,
            'accuracy': round(accuracy, 2),
            'won_count': sum(1 for r in records if r.is_won),
            'lost_count': sum(1 for r in records if not r.is_won)
        }
    
    def analyze_performance(self) -> FeedbackAnalysis:
        """分析模型性能"""
        stats = self.get_accuracy_stats()
        
        statement = select(BidRecord).where(BidRecord.actual_result != '待定')
        records = self.db.exec(statement).all()
        
        high_score_won = sum(1 for r in records if r.predicted_score >= 60 and r.is_won)
        high_score_lost = sum(1 for r in records if r.predicted_score >= 60 and not r.is_won)
        low_score_won = sum(1 for r in records if r.predicted_score < 60 and r.is_won)
        low_score_lost = sum(1 for r in records if r.predicted_score < 60 and not r.is_won)
        
        recommendations = self._generate_recommendations(
            stats['accuracy'], high_score_lost, low_score_won
        )
        
        analysis = FeedbackAnalysis(
            total_records=stats['total'],
            correct_predictions=stats['correct'],
            accuracy=stats['accuracy'],
            high_score_won=high_score_won,
            high_score_lost=high_score_lost,
            low_score_won=low_score_won,
            low_score_lost=low_score_lost,
            recommendations=recommendations
        )
        
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        
        return analysis
    
    def _generate_recommendations(
        self, 
        accuracy: float, 
        high_score_lost: int, 
        low_score_won: int
    ) -> str:
        """生成优化建议"""
        recs = []
        
        if accuracy < 0.5:
            recs.append("预测准确性较低，建议重新评估评分权重")
        
        if high_score_lost > 2:
            recs.append("存在多次高分预测但未中标，建议分析失败原因")
        
        if low_score_won > 2:
            recs.append("存在多次低分预测但中标，建议降低评分门槛")
        
        return "; ".join(recs) if recs else "模型表现正常"
    
    def get_recent_records(self, limit: int = 10) -> List[BidRecord]:
        """获取最近的投标记录"""
        statement = (
            select(BidRecord)
            .order_by(BidRecord.created_at.desc())
            .limit(limit)
        )
        return self.db.exec(statement).all()
    
    def get_records_by_tender(self, tender_id: int) -> List[BidRecord]:
        """获取指定项目的投标记录"""
        statement = select(BidRecord).where(BidRecord.tender_id == tender_id)
        return self.db.exec(statement).all()
