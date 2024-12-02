from PyQt5  import QtWidgets
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import librosa.display
from scipy.signal import spectrogram


class spec_Widget(QWidget):
    def __init__(self, parent=None):
        # create vertical layout >>put it the canvas and set this layout to the Qwidget
        super().__init__(parent)
        self.canvas = FigureCanvas(Figure(facecolor='none'))
        
        # self.setGeometry(830, 450, 1011, 371)
        self.canvas.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.canvas.axes.axis('off')
        # # Set the color of the axes to white
        # self.canvas.axes.tick_params(axis='both', colors='white')
        self.setLayout(vertical_layout)



    def plot_spectrogram(self, data, sample_rate, title='Spectrogram', x_label='Time', y_label='Frequency'):

        spectrogram = librosa.amplitude_to_db(
            np.abs(librosa.stft(data)), ref=np.max)
        librosa.display.specshow(
            spectrogram, sr=sample_rate, x_axis='time', y_axis='log', ax=self.canvas.axes)
        self.canvas.draw()

    def clear(self):
        self.canvas.axes.clear()
        self.canvas.draw()