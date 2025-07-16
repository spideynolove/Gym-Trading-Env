import sys
sys.path.append('./src')
import pandas as pd
from gym_trading_env.renderer import Renderer
renderer = Renderer(render_logs_dir='render_logs')
renderer.run()