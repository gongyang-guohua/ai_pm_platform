from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.project import Task

class EVMService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_project_metrics(self, project_id: int):
        """
        Calculates project-level Earned Value Management (EVM) metrics.
        """
        result = await self.session.execute(
            select(Task).where(Task.project_id == project_id)
        )
        tasks = result.scalars().all()
        
        sum_pv = sum(t.planned_value for t in tasks)
        sum_ev = sum(t.earned_value for t in tasks)
        sum_ac = sum(t.actual_cost for t in tasks)
        sum_bac = sum(t.budget_at_completion for t in tasks)
        
        # Efficiency Indicators
        spi = sum_ev / sum_pv if sum_pv > 0 else 1.0
        cpi = sum_ev / sum_ac if sum_ac > 0 else 1.0
        
        # Variances
        sv = sum_ev - sum_pv # Schedule Variance
        cv = sum_ev - sum_ac # Cost Variance
        
        # Forecasts
        eac = sum_bac / cpi if cpi > 0 else sum_bac
        etc = eac - sum_ac
        
        return {
            "project_id": project_id,
            "SPI": round(spi, 3),
            "CPI": round(cpi, 3),
            "SV": round(sv, 2),
            "CV": round(cv, 2),
            "BAC": round(sum_bac, 2),
            "PV_total": round(sum_pv, 2),
            "EV_total": round(sum_ev, 2),
            "AC_total": round(sum_ac, 2),
            "EAC": round(eac, 2),
            "ETC": round(etc, 2),
            "status": "on_track" if spi >= 1.0 and cpi >= 1.0 else "at_risk"
        }
