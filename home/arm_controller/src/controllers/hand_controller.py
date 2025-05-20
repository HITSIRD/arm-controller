# import impire_hand_wr_tactile as hand_wr

class HandController:
    def __init__(self, hand):
        self.hand = hand

    # def read_angles(self):
    #     return hand_wr.read6(self.client, "angleAct")
    #
    # def read_forces(self):
    #     return hand_wr.read6(self.client, "forceAct")
    #
    def read_width(self):
        return self.hand.read_once().width

    def grasp(self, object):

        return self.hand.grasp(object)