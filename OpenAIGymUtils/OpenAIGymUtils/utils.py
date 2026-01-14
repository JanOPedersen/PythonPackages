import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

def ParseMaze(maze_path):
    '''Parse the maze XML file and return a dictionary with its contents.'''
    tree = ET.parse(maze_path)  # Load the XML file
    root = tree.getroot()
    maze_dict = {}
    maze_dict['name'] = maze_path.split('\\')[-1].split('.')[0]  # Extract the maze name from the file path

    for elem in root:
        match elem.tag:
            case "dimensions":
                maze_dict['Width'] = int(elem.find('Width').text)
                maze_dict['Height'] = int(elem.find('Height').text)
            case "HorizontalWalls":
                HorizontalWalls = []
                for cell in elem.findall('Wall'):
                    HorizontalWalls.append((int(cell.find('x').text), int(cell.find('y').text)))
                maze_dict['HorizontalWalls'] = HorizontalWalls
            case "VerticalWalls":
                VerticalWalls = []
                for cell in elem.findall('Wall'):
                    VerticalWalls.append((int(cell.find('x').text), int(cell.find('y').text)))
                maze_dict['VerticalWalls'] = VerticalWalls
            case "Unreachable":
                Unreachable = []
                for cell in elem.findall('Cell'):
                    Unreachable.append((int(cell.find('x').text), int(cell.find('y').text)))
                maze_dict['Unreachable'] = Unreachable
            case "Reward":
                Reward = []
                for cell in elem.findall('Cell'):
                    Reward.append((int(cell.find('x').text), int(cell.find('y').text), float(cell.find('reward').text)))
                maze_dict['Reward'] = Reward
            case "Punishment":
                maze_dict['Punishment'] = float(elem.text.strip())
            case "Terminal":
                Terminal = []
                for cell in elem.findall('Cell'):
                    Terminal.append((int(cell.find('x').text), int(cell.find('y').text)))
                maze_dict['Terminal'] = Terminal

    return maze_dict

def PlotMaze(maze_dict):
    '''Plot the maze using matplotlib based on the parsed dictionary.'''
    Width = maze_dict['Width']
    Height = maze_dict['Height']
    maze = np.zeros((Height, Width))

    for (x,y) in maze_dict['Unreachable']:
        maze[x - 1, y - 1] = 1

    letters = [[' ' for _ in range(Width)] for _ in range(Height)]
    for (x,y,r) in maze_dict['Reward']: 
        letters[x - 1][y - 1] = 'F'  if r > 0 else 'E' if r < 0 else ' '

    # Desired pixel dimensions
    width_px = 800
    height_px = width_px * Height / Width
    dpi = 100  # dots per inch

    # Plot the maze
    # Convert pixels to inches
    _, ax = plt.subplots(figsize=(width_px / dpi, height_px / dpi), dpi=dpi)
    ax.imshow(maze, cmap=ListedColormap(['white','grey']), interpolation='none')

    # Loop through data and place text annotations
    for i in range(Height):
        for j in range(Width):
            ax.text(j, i, letters[i][j], ha='center', va='center', color='black', fontsize=16)

    # Draw lines inside the cells
    for i in range(1, Width + 1):
        ax.axvline(i - 0.5, color='black', linewidth=0.8)
    for i in range(1, Height + 1):
        ax.axhline(i - 0.5, color='black', linewidth=0.8)

    for (x,y) in maze_dict['HorizontalWalls']:
        ax.plot([x - 1.5, x - 0.5], [y - 1.5, y - 1.5], color='black', linewidth=4)

    for (x,y) in maze_dict['VerticalWalls']:
        ax.plot([x - 1.5, x - 1.5], [y - 1.5, y - 0.5], color='black', linewidth=4)

    ax.set_xticks([])
    ax.set_yticks([])

    plt.title(maze_dict['name'])
    plt.show()

def calculateMazeAscii(maze_dict):
    '''represents the maze as a list of strings'''
    Width = maze_dict['Width']
    Height = maze_dict['Height']
    maze = [[' ' for _ in range(Width)] for _ in range(Height)]
    for (x,y,r) in maze_dict['Reward']: 
        maze[x - 1][y - 1] = 'F'  if r > 0 else 'E' if r < 0 else ' '

    for (x,y) in maze_dict['Unreachable']:
        maze[x - 1][y - 1] = '#'

    string_maze = []
    for row in maze:
        string_maze.append("".join(row))

    return string_maze    

def plotAsciiMaze(ascii_maze):
    '''prints the maze in ASCII format'''
    for row in ascii_maze:
        print(row)