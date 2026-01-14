from __future__ import annotations

from minigrid.core.grid import Grid
from minigrid.core.world_object import Door, Goal, Key, Wall
from minigrid.minigrid_env import MiniGridEnv
from minigrid.core.mission import MissionSpace
from minigrid.manual_control import ManualControl
from OpenAIGymUtils.OpenAIGymUtils.utils import ParseMaze
import numpy as np
import pygame

class MazeEnv(MiniGridEnv):
    def __init__(self, maze_path=None, **kwargs):
        '''In the below super().__init__(...) call, we cannot set both gridsize and (width, height)'''
        self.maze_path = maze_path
        self.maze_dict = ParseMaze(maze_path) if maze_path else None
        self.width = self.maze_dict['Width'] + 2  # Adding 2 for walls
        self.height = self.maze_dict['Height'] + 2  # Adding 2 for walls
        mission_space = MissionSpace(mission_func=self._gen_mission)
        super().__init__(mission_space=mission_space, max_steps=100, width=self.width, height=self.height, **kwargs)

    @staticmethod
    def _gen_mission():
        return "Reach the goal!"

    def _gen_grid(self, width, height):
        self.grid = Grid(self.width, self.height)
        self.grid.wall_rect(0, 0, self.width, self.height)

        for (x,y) in self.maze_dict['Unreachable']:
            self.grid.set(y, x, Wall())

        for (x,y,r) in self.maze_dict['Reward']: 
            self.put_obj(Goal(), y, x)
            
        self.place_agent()

    def render(self):
        if self.render_mode == "human":
            img = self.get_frame(self.highlight, self.tile_size, self.agent_pov)
            img = np.transpose(img, axes=(1, 0, 2))
            if self.render_size is None:
                self.render_size = img.shape[:2]
            if self.window is None:
                pygame.init()
                pygame.display.init()
                self.window = pygame.display.set_mode(
                    (img.shape[0], img.shape[1])  
                )
                pygame.display.set_caption(self.maze_dict['name'])
            if self.clock is None:
                self.clock = pygame.time.Clock()
            surf = pygame.surfarray.make_surface(img)
            
            # Create background with mission description
            bg = pygame.Surface(
                (int(surf.get_size()[0]), int(surf.get_size()[1]))
            )
            bg.convert()
            bg.fill((255, 255, 255))
            bg.blit(surf, (0,0))
            bg = pygame.transform.smoothscale(bg, surf.get_size())

            self.window.blit(bg, (0, 0))
            pygame.event.pump()
            self.clock.tick(self.metadata["render_fps"])
            pygame.display.flip()
            return

        elif self.render_mode == "rgb_array":
            # Return an image array
            return super().render()
        
        elif self.render_mode == "custom":
            # Return an image array
            return super().render()
        else:
            # Custom fallback or error
            return None