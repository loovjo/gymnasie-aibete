import pygame
from util import * 
 
class HumanAgent:
    def __init__(self,ui):
        self.ui = ui

    def getAction(self, agentInput):
        if pygame.K_SPACE in self.ui.pressedKeys:
            return Actions.JUMP
        if pygame.K_RIGHT in self.ui.pressedKeys:
            return Actions.RIGHT
        if pygame.K_LEFT in self.ui.pressedKeys:
            return Actions.LEFT
        if pygame.K_r in self.ui.pressedKeys:
            return Actions.RESTART
        return Actions.NONE

    def getActions(self, agentInputs):
        if pygame.K_SPACE in self.ui.pressedKeys:
            return [Actions.JUMP]
        if pygame.K_RIGHT in self.ui.pressedKeys:
            return [Actions.RIGHT]
        if pygame.K_LEFT in self.ui.pressedKeys:
            return [Actions.LEFT]
        if pygame.K_r in self.ui.pressedKeys:
            return [Actions.RESTART]
        return [Actions.NONE]


    def update(self, agentInput,action,newAgentInput,reward):
        pass
