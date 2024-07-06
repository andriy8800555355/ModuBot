from pyrogram import Client, filters
import sympy as sp
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from io import BytesIO

def add_on_commands(app: Client):
    # Math operations with sympy
    @app.on_message(filters.command("math", prefixes="."))
    def math_command(client, message):
        try:
            expression = message.text.split(' ', 1)[1]  # Extract expression after the command
            # Replace common notations for better compatibility with sympy
            expression = expression.replace('^', '**')
            result = sp.sympify(expression)
            # Check if the expression is an equality
            if isinstance(result, sp.Equality):
                is_equal = sp.simplify(result.lhs - result.rhs) == 0
                message.reply_text(f"The expression is {'correct' if is_equal else 'incorrect'}: {result}")
            else:
                if result == 300:
                    message.reply_photo(photo='NOPE.jpg')
                else:
                    message.reply_text(f"{result}")
        except IndexError:
            message.reply_text("Please provide a valid mathematical expression.")
        except sp.SympifyError:
            message.reply_text("There was an error evaluating the expression. Please check your input.")
        except Exception as e:
            message.reply_text(f"An unexpected error occurred: {e}")

    # Plotting
    @app.on_message(filters.command("plot", prefixes="."))
    def plot_command(client, message):
        try:
            data = message.text.split(' ', 1)[1]  # Extract data after the command
            points = list(map(float, data.split()))
            # Separate x and y coordinates
            x_coords = points[0::2]
            y_coords = points[1::2]
            plt.plot(x_coords, y_coords, marker='o')
            plt.title("Plot")
            plt.xlabel("x")
            plt.ylabel("y")
            plt.grid(True)
            plt.axis('equal')  # Set equal scaling to maintain shape proportions
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            message.reply_photo(photo=buf)
            plt.close()
        except (ValueError, IndexError):
            message.reply_text("Please provide valid numbers in the format x1 y1 x2 y2 ...")
        except Exception as e:
            message.reply_text(f"An unexpected error occurred: {e}")

    # 3D Cube Plotting
    @app.on_message(filters.command("cube", prefixes="."))
    def cube_command(client, message):
        try:
            # Define vertices of a 3D cube
            vertices = [
                [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
                [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
            ]
            
            # Define the edges connecting the vertices
            edges = [
                [vertices[0], vertices[1]], [vertices[1], vertices[2]], [vertices[2], vertices[3]], [vertices[3], vertices[0]],
                [vertices[4], vertices[5]], [vertices[5], vertices[6]], [vertices[6], vertices[7]], [vertices[7], vertices[4]],
                [vertices[0], vertices[4]], [vertices[1], vertices[5]], [vertices[2], vertices[6]], [vertices[3], vertices[7]]
            ]

            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')

            for edge in edges:
                xs, ys, zs = zip(*edge)
                ax.plot(xs, ys, zs, marker='o')

            ax.set_title("3D Cube")
            buf = BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            message.reply_photo(photo=buf)
            plt.close()
        except Exception as e:
            message.reply_text(f"An unexpected error occurred: {e}")