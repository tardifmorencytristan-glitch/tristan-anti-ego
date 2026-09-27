import unittest
from tristan_anti_ego.core import *

class AntiEgoTests(unittest.TestCase):
    def s(self,cid="x",origin="TRISTAN",**kw):
        base=dict(candidate_id=cid,origin=origin,family="SOLVER",value=1,evidence=.8,uncertainty_reduction=.2,future_work_destroyed=.3,proof_reuse=.2,complexity=.2,latency=.1,maintenance_cost=.1,irreversibility=.1,blast_radius=.1,authority_risk=0)
        base.update(kw); return Submission(**base)
    def test_origin_does_not_change_blind_token(self):
        self.assertEqual(self.s("a","TRISTAN").blind_token,self.s("b","EXTERNAL").blind_token)
    def test_origin_does_not_change_score(self):
        self.assertEqual(score(self.s("a","TRISTAN")),score(self.s("b","EXTERNAL")))
    def test_no_action_injected(self):
        self.assertEqual(blind_court([]).status,"NO_ACTION_WINS")
    def test_harmful_candidate_loses(self):
        self.assertEqual(blind_court([self.s(value=-10,complexity=10)]).status,"NO_ACTION_WINS")
    def test_good_candidate_wins_and_reveals(self):
        s=self.s("good","EXTERNAL",value=5,future_work_destroyed=2)
        self.assertEqual(reveal(blind_court([s]),[s]).candidate_id,"good")
    def test_authority_risk_blocks(self):
        self.assertFalse(evaluate(self.s(authority_risk=.1)).eligible)
    def test_right_to_die(self):
        self.assertEqual(right_to_die(VitalityHistory("x",5,0,0,0,5,0,2,True)),"RIGHT_TO_DIE")
    def test_ablation_can_reward_removal(self):
        self.assertGreater(ablation_value(1,1.1,.2),0)

if __name__=="__main__": unittest.main()
