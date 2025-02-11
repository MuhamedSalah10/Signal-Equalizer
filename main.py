import librosa
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow , QFileDialog
import pyqtgraph as pg
import numpy as np
import sounddevice as sd
import sys
from PyQt5 import uic
import time
from PyQt5.QtCore import Qt
from Mode import mode
from Spec_Widget_New import spec_Widget
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget , QDesktopWidget
from scipy.fft import fft, ifft, fftfreq
import pandas as pd
import copy
import pyqtgraph as pg
Ui_MainWindow, QtBaseClass = uic.loadUiType("equalizer.ui")

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        screen_size=QDesktopWidget().screenGeometry()
        width=screen_size.width()
        height=screen_size.height()
        self.setGeometry(0,0,width , height-100)
        
        self.pushButton_After_signal_1.clicked.connect(lambda : self.play_filterd_signal(0))
        self.pushButton_signal_1.clicked.connect(lambda : self.play_noisy_signal(0))

        self.pushButton_After_signal_2.clicked.connect(lambda : self.play_filterd_signal(1))
        self.pushButton_signal_2.clicked.connect(lambda : self.play_noisy_signal(1))

        self.pushButton_After_signal_3.clicked.connect(lambda : self.play_filterd_signal(2))
        self.pushButton_signal_3.clicked.connect(lambda : self.play_noisy_signal(2))

        self.PushButton_Select.clicked.connect(self.Select_Part)

        animal_frequncy_slices={self.VerticalSlider_Channel_10:[7600, 20000]
             ,self.VerticalSlider_Channel_8:[2200, 8800]
             ,self.VerticalSlider_Channel_6:[1800,2300]
             ,self.VerticalSlider_Channel_4:[500, 1900]
             ,self.VerticalSlider_Channel_2:[0, 500]}
        


        # instead of Musiccc
        Second_Mode_Slices={
              self.VerticalSlider_Channel_3:[2300, 3500] #for E
             ,self.VerticalSlider_Channel_4:[1500,4000]  # for Drums
             ,self.VerticalSlider_Channel_6:[150, 2000]  # for I
             ,self.VerticalSlider_Channel_7:[1500, 3000]   #for O
             ,self.VerticalSlider_Channel_8:[50,2000] #for piano

       }

        self.Weiner_Noise=[["Data\\Weiner_Data\\filtered_1.wav" , "Data\\Weiner_Data\\song_final_1.wav"],
                           [ "Data\\Weiner_Data\\filtered_2.wav","Data\\Weiner_Data\\song_final_2.wav"],
                           ["Data\\Weiner_Data\\filtered_3.wav" ,"Data\\Weiner_Data\\song_final_3.wav"]]

        self.Weiner_Orginal_Signals_data=[[]
        ,[],[]]

        self.Calculate_Weiner_orginal_data()
        
        self.Rec=None
        
        self.freq_tst={self.VerticalSlider_Channel_3:[200, 2000]
             ,self.VerticalSlider_Channel_4:[50,2000]  # for Drums
             ,self.VerticalSlider_Channel_5:[0 ,3000]
             ,self.VerticalSlider_Channel_6:[1300, 4200]  # for vilons
             ,self.VerticalSlider_Channel_8:[3500,5000] #for piano
             }
        
  
        self.speed_factor=1
        self.tracking_index=0
        self.last_ind=0
        self.num_frames=0

        #assigin
        animal_obj=mode("Data/musicAndAnimal.wav",True)
        animal_obj.freq_slices=animal_frequncy_slices
        
        music_obj=mode("Data/Music_Mode.wav",True)
        music_obj.freq_slices=Second_Mode_Slices

        self.uniform_obj=mode("Data/UniformSignal.csv",False)
        self.uniform_obj.freq_slices=None
        
        weiner_obj=mode("Data/Weiner_Data/song_final_1.wav" , True)
        weiner_obj.freq_slices=self.freq_tst

        self.mode=self.uniform_obj 
        self.mode.timer.start()
        self.mode.timer.timeout.connect(self.update_plot)
        self.ComboBox_Mode.setItemData(0, self.uniform_obj, Qt.UserRole)
        self.ComboBox_Mode.setItemData(1, music_obj, Qt.UserRole)
        self.ComboBox_Mode.setItemData(2, animal_obj, Qt.UserRole)
        self.ComboBox_Mode.setItemData(3, weiner_obj, Qt.UserRole)

     
        self.plot_input = self.Widget_Signal_Input.plot(pen="r")
        self.plot_output= self.Widget_Signal_Output.plot(pen="r")


        self.checkBox.stateChanged.connect(self.toggle_spectrograms_visibility)
        


        self.ComboBox_Mode.currentIndexChanged.connect(lambda index :self.Change_mode(index))
        self.comboBox_Frequancy_Scale.currentIndexChanged.connect(self.plot_frequency_spectrum)
        self.PushButton_Reset_Input.clicked.connect(lambda:self.reset())
        
        self.PushButton_PlayPause_Input.clicked.connect(lambda:self.play_pause())
        self.PushButton_Upload_Signal.clicked.connect(lambda: self.Load_Weiner_Signal())
       
        self.HorizontalSlider_Speed_Input.setMinimum(2)
        self.HorizontalSlider_Speed_Input.setMaximum(40)
        self.HorizontalSlider_Speed_Input.setSingleStep(5)
        self.HorizontalSlider_Speed_Input.setValue(10)
        self.HorizontalSlider_Speed_Input.valueChanged.connect(lambda:self.set_speed())
        self.PushButton_ZoomIn_Input.clicked.connect(lambda : self.zoom_in())
        self.PushButton_Zoomout_Input.clicked.connect(lambda : self.zoom_out())


        for i in range(1, 11):
            getattr(self, f"VerticalSlider_Channel_{i}").valueChanged.connect(lambda _, i=i: self.apply_attenuation(getattr(self, f"VerticalSlider_Channel_{i}"), i))

        
        self.spectrogram_widget1 = spec_Widget()
        self.spectrogram_widget2 = spec_Widget()

        # Set up layouts for spectrogram widgets
        self.setup_widget_layout(self.spectrogram_widget1, self.Widget_Spectrogram_Input)
        self.setup_widget_layout(self.spectrogram_widget2, self.Widget_Spectrogram_Output)

        self.Change_mode(0)



        
    
    def setup_widget_layout(self, spec_widget, target_widget):
        if isinstance(target_widget, QWidget):
            layout = QVBoxLayout(target_widget)
            layout.addWidget(spec_widget)
            target_widget.setLayout(layout)  
        else:
   
            print("Target widget is not a valid QWidget")

    def browse_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;CSV Files (*.csv);;DAT Files (*.dat);;XLSX Files (*.xlsx);;TXT Files (*.txt)", options=options)
        
        if fileName:
            print(f"Selected file: {fileName}")
            try:
                return fileName
            except Exception as e:
                print(f"Error opening file: {e}")
                return None
        else:
            print("No file selected")
            return None
  
    
    def Load_Weiner_Signal(self):
        pass


    def Change_mode(self , index):
        self.HorizontalSlider_Speed_Input.setValue(10)
        self.PushButton_PlayPause_Input.setText("Pause")
        if self.mode.audio:
            self.stream.stop()
        self.mode.timer.stop()
        self.mode = self.ComboBox_Mode.itemData(index, Qt.UserRole)

        self.tracking_index=self.mode.tracking_index
        self.frequncies=np.fft.fftfreq(len(self.mode.signal.amplitude), 1 / self.mode.signal.sample_rate) 
        self.fft_result = np.fft.fft( self.mode.signal.amplitude)

        self.isplay=self.mode.isplaying
        self.timer=self.mode.timer
        self.mode.timer.timeout.connect(self.update_plot)

        self.mode.timer.start()
        self.audio_data = self.mode.audio_data
        self.modified_audio=self.audio_data
        if  self.checkBox.isChecked():
            self.spectrogram_widget1.plot_spectrogram(self.mode.signal.amplitude, self.mode.signal.sample_rate )
            self.spectrogram_widget2.plot_spectrogram(self.mode.signal.amplitude, self.mode.signal.sample_rate )
       
        self.cumulative_attenuation =  np.ones((10, len(self.audio_data)))
       
        self.audio_data_stretched=self.audio_data
        self.original_audio_data=self.audio_data

        if self.mode.audio:
            self.stream = sd.OutputStream(
            samplerate=self.mode.signal.sample_rate,
            channels=1,
            callback=self.audio_callback)
            self.stream.start()

        # self.calculate_fft()
        self.Reset_slider()
        self.setup_sliders()

        self.timer.start()
        self.plot_frequency_spectrum()


        # calculate the ranges of the signal  >>> calculate for all modes but used only in normal
        self.uniform_ranges=self.get_range_frequencies()
        # print(f" the ranges is : {self.uniform_ranges}")
        self.uniform_frequncy_slices ={
             getattr(self, f"VerticalSlider_Channel_{i}"): self.uniform_ranges[i - 1]
            for i in range(1, 11)}
        self.uniform_obj.freq_slices=self.uniform_frequncy_slices
    

    def reset(self):
        self.tracking_index=0
        self.timer.start()
        self.PushButton_PlayPause_Input.setText("Pause")
        self.isplay=True
        if self.mode.audio:
            self.stream.start()

       
        
    def play_pause(self):
        if self.isplay:
            self.isplay=False
            self.timer.stop()
            self.PushButton_PlayPause_Input.setText("play")
            if self.mode.audio:
                self.stream.stop()
        else:
            self.isplay=True
            self.timer.start()
            self.PushButton_PlayPause_Input.setText("Pause")
            if self.mode.audio:
                self.stream.start()

    def set_speed(self):
        value=self.HorizontalSlider_Speed_Input.value()
        self.old_speed_factor=self.speed_factor
        self.speed_factor=value/10
        self.audio_data_stretched = librosa.effects.time_stretch(self.modified_audio, rate=self.speed_factor)
        self.tracking_index*=(self.old_speed_factor/self.speed_factor)
        self.tracking_index=int(self.tracking_index)
        
        
        


    def audio_callback(self, outdata, frames, time, status):
        """Callback function to send audio in chunks to the OutputStream."""
        # print(frames)
        
        self.mode.frames=frames

        end_index = self.tracking_index + (frames)
        remaining_samples = len(self.audio_data_stretched) - self.tracking_index
        try :
            # Ensure that the end index is within the bounds of the audio data
            if end_index <= len(self.audio_data_stretched):
                # If the end_index is within bounds, copy data directly
                # print(self.tracking_index,end_index)
                outdata[:, 0] = self.audio_data_stretched[self.tracking_index:end_index]
                
            
            else:
                # If end_index is out of bounds, copy the remaining samples
                if remaining_samples > 0:
                    outdata[:remaining_samples, 0] = self.audio_data_stretched[self.tracking_index:]

                if remaining_samples < frames:
                    outdata[remaining_samples:, 0] = 0


            self.tracking_index = end_index
            if self.tracking_index >= len(self.audio_data_stretched):
                self.stream.stop()  # Stop playback when done

        except:
            print("dcvmcndv")




    def update_plot(self):
        # Plot current chunk of data up to the tracking index for progress display
        tracking_index=int(self.tracking_index*self.speed_factor)
        # print(f" the firsttt is the modified  : {self.mode.signal.amplitude.shape}")
        # print(f"the second plot : {self.modified_audio.shape}")
        if tracking_index < len(self.mode.signal.amplitude) :
            
            # Plot progress using a separate line over the waveform
            self.plot_input.setData((self.mode.signal.time[:tracking_index]), self.mode.signal.amplitude[:tracking_index])
            self.plot_output.setData((self.mode.signal.time[:tracking_index]), self.modified_audio[:tracking_index])
            if not self.mode.audio and tracking_index < len(self.mode.signal.amplitude):
                self.tracking_index+=self.mode.frames   
                # self.speed_factor=1
            
        else:
            self.timer.stop()


    
    def attenuate_frequency_range(self, freq_start, freq_end, attenuation_factor,index):
        """Apply attenuation to the cumulative attenuation array based on frequency range and factor."""
        # fft_result = np.fft.fft(self.original_audio_data)
        frequencies = self.frequncies
        
        # Identify indices within the frequency range and apply the attenuation factor
        indices = np.where((frequencies >= freq_start) & (frequencies <= freq_end))[0]
        self.cumulative_attenuation[index-1][indices] *= attenuation_factor
        self.cumulative_attenuation[index-1][-indices] *= attenuation_factor  # Apply to negative frequencies as well
        

    def apply_attenuation(self,slider_obj,index):
        fft_result=None
        """Update the audio signal with cumulative attenuation from each slider."""
        # Reset cumulative attenuation before applying new values
        self.cumulative_attenuation[index-1] = np.ones(len(self.audio_data))
        # print(self.mode.freq_slices.keys())
        # Apply each slider’s attenuation range
        # print(self.mode.freq_slices[slider_obj][1])
        self.attenuate_frequency_range(self.mode.freq_slices[slider_obj][0], self.mode.freq_slices[slider_obj][1], slider_obj.value() / 100,index)
        fft_result =copy.copy (self.fft_result)
        
        for i in range(10):
            fft_result *= self.cumulative_attenuation[i] 
        self.modified_audio = np.fft.ifft(fft_result).real
        self.set_speed()
        self.plot_frequency_spectrum()
        if  self.checkBox.isChecked():
            self.spectrogram_widget2.plot_spectrogram(self.modified_audio, self.mode.signal.sample_rate )
    


    def get_range_frequencies(self):
            """Extracts the top frequencies by magnitude from the signal."""

            # Copy FFT result and calculate frequencies
            fft_result = copy.copy(self.fft_result)
            frequencies = np.fft.fftfreq(len(fft_result), 1 / self.mode.signal.sample_rate)

            # Filter positive frequencies and their magnitudes
            positive_frequencies = frequencies[frequencies >= 0]
            fft_result = np.abs(fft_result[frequencies >= 0])

            # Set the threshold as 10% of the maximum frequency magnitude
            max_magnitude = np.max(fft_result)
            threshold = 0.1 * max_magnitude

            # Filter frequencies and magnitudes above the threshold
            filtered_indices = np.where(fft_result >= threshold)[0]
            filtered_frequencies = positive_frequencies[filtered_indices]
            filtered_magnitudes = fft_result[filtered_indices]

            # Sort the filtered frequencies and magnitudes based on frequency values
            sorted_indices = np.argsort(filtered_frequencies)
            sorted_filtered_frequencies = filtered_frequencies[sorted_indices]
            # sorted_filtered_magnitudes = filtered_magnitudes[sorted_indices]

            # Split the filtered frequencies into 10 roughly equal ranges
            num_bands = 10
            total_frequencies = len(sorted_filtered_frequencies)
            band_size = total_frequencies // num_bands

            # Create frequency ranges
            freq_bands = []
            for i in range(num_bands):
                start_index = i * band_size
                # Handle last band case to include all remaining frequencies
                end_index = (i + 1) * band_size if i != num_bands - 1 else total_frequencies
                band_frequencies = sorted_filtered_frequencies[start_index:end_index]
                # Determine range for this band
                if band_frequencies.size > 0:
                    band_range = [band_frequencies[0], band_frequencies[-1]]
                else:
                    band_range = [0, 0]
                freq_bands.append(band_range)

            return freq_bands


    def plot_frequency_spectrum(self):
        index=self.comboBox_Frequancy_Scale.currentIndex()
        """Plot the frequency spectrum of the modified audio."""
        fft_result = np.fft.fft(self.modified_audio)
        # print(1 / self.mode.signal.sample_rate  , len(fft_result))
        frequencies = np.fft.fftfreq(len(fft_result), (1 / self.mode.signal.sample_rate))
        magnitude = np.abs(fft_result)
        
        self.Widget_Frequancy.clear()
        pos_frequencies = frequencies[:len(frequencies)//2]
        pos_magnitude = magnitude[:len(magnitude)//2]
        
        
        sr=self.mode.signal.sample_rate
        log_frequency_bands = np.logspace(np.log10(50), np.log10(sr // 2), num=50)
        band_amplitudes = []

        # Calculate the average amplitude in each frequency band
        for band in log_frequency_bands:
            # Find indices of the frequencies that fall within each band
            band_indices = np.where((pos_frequencies >= band - 50) & (pos_frequencies <= band + 50))
            band_magnitude = np.mean(magnitude[band_indices])
            band_amplitudes.append(band_magnitude)
        if index==0:
            pos_plot = pg.PlotDataItem(pos_frequencies, pos_magnitude, pen=pg.mkPen('b', width=2))
        else: 
            pos_plot = pg.PlotDataItem(log_frequency_bands, band_amplitudes, pen=pg.mkPen('b', width=2))
        
        self.Widget_Frequancy.addItem(pos_plot)


        


    def toggle_spectrograms_visibility(self):
        # Check if the checkbox is checked
        if self.checkBox.isChecked():
            # Show the spectrogram widgets
            self.Widget_Spectrogram_Input.show()
            self.Widget_Spectrogram_Output.show()
        else:
            # Hide the spectrogram widgets
            self.Widget_Spectrogram_Input.hide()
            self.Widget_Spectrogram_Output.hide()
    
    def Reset_slider(self):
        index=self.ComboBox_Mode.currentIndex()
        if index==0:
            self.Widget_Frequancy.setXRange(0,120)
            for i in range(1, 11):
                getattr(self, f"VerticalSlider_Channel_{i}").setValue(100)
        elif index== 1 or index==2 or index==3:
            for i in range(2 , 10 , 2):
                getattr(self, f"VerticalSlider_Channel_{i}").setValue(100)
        # music
        if index==1:
            self.Widget_Frequancy.setXRange(18,11000)
        # animal
        if index==2:
            self.Widget_Frequancy.setXRange(0,10000)
            # ECG
        if index==3:
            # for i in range(4 , 10 , 2):
            #     getattr(self, f"VerticalSlider_Channel_{i}").setValue(0)
            self.Widget_Frequancy.setXRange(0,1000)


        self.HorizontalSlider_Speed_Input.setValue(10)

    


    def setup_sliders(self):
        if self.ComboBox_Mode.currentText() == 'Uniform Range Mode':
            self.frame_17.show()
            self.frame_19.show()
            self.frame_21.show()
            self.frame_23.show()
            self.frame_25.show()
            self.frame_26.show()
            self.frame_18.show()
            self.frame_20.show()
            self.frame_22.show()
            self.frame_24.show()

            self.label_6.setText("Ch(1)")
            self.label_8.setText("Ch(2)")
            self.label_12.setText("Ch(3)")
            self.label_14.setText("Ch(4)")
            self.label_16.setText("Ch(5)")
            self.label_18.setText("Ch(6)")
            self.label_20.setText("Ch(7)")
            self.label_22.setText("Ch(8)")
            self.label_24.setText("Ch(9)")
            self.label_26.setText("Ch(10)")

            
            self.remove_weiner_buttons()

        
        elif self.ComboBox_Mode.currentText() == 'Weiner Mode':
            # self.Weiner_Button.show()
            self.frame_17.hide()
            self.frame_18.hide()
            self.frame_19.hide()
            self.frame_20.hide()
            self.frame_21.hide()
            self.frame_22.hide()
            self.frame_23.hide()
            self.frame_24.hide()
            self.frame_25.hide()
            self.frame_26.hide()

            self.show_weiner_buttons()


        elif self.ComboBox_Mode.currentText() == 'Musical Instruments Mode':
            self.frame_17.hide()
            self.frame_18.hide()
            self.frame_25.hide()
            self.frame_26.hide()
            self.frame_21.hide()

            self.frame_19.show()
            self.frame_20.show()           
            self.frame_22.show()
            self.frame_23.show()
            self.frame_24.show()

            self.label_12.setText("E")
            self.label_14.setText("Drums")
            self.label_18.setText("I")
            self.label_20.setText("O")
            self.label_22.setText("Piano")    


            self.remove_weiner_buttons()
        else :
            
            self.frame_17.hide()
            self.frame_19.hide()
            self.frame_21.hide()
            self.frame_23.hide()
            self.frame_25.hide()
            # self.frame_26.hide()

            self.frame_18.show()
            self.frame_20.show()
            self.frame_22.show()
            self.frame_24.show()
            self.frame_26.show()


            # self.Weiner_Button.hide()

            self.label_8.setText("Bass")
            self.label_14.setText("Flute")
            self.label_18.setText("Bird")
            self.label_22.setText("Monkey")
            self.label_26.setText("Bat")

            self.remove_weiner_buttons()


    def remove_weiner_buttons(self):
        self.frame_button_1.hide()
        self.frame_button_2.hide()
        self.frame_button_3.hide()
        self.PushButton_Select.hide()



    def show_weiner_buttons(self):
        self.frame_button_1.show()
        self.frame_button_2.show()
        self.frame_button_3.show()
        self.PushButton_Select.show()


    def zoom_in(self ) :
        viewboxI=self.Widget_Signal_Input.getViewBox()
        viewboxO=self.Widget_Signal_Output.getViewBox()
        viewboxI.scaleBy((.8,.8))
        viewboxO.scaleBy((0.8,.8))


    def zoom_out(self):
           viewboxI=self.Widget_Signal_Input.getViewBox()
           viewboxO=self.Widget_Signal_Output.getViewBox()
           viewboxI.scaleBy((1/0.8, 1/0.8))
           viewboxO.scaleBy((1/0.8, 1/0.8))

    def play_filterd_signal(self, num):
            signal=self.Weiner_Noise[num][0]
            Weiner_obj=mode(signal , True)
            Weiner_obj.freq_slices=self.freq_tst
            self.mode=Weiner_obj 
            self.mode.timer.start()
            self.mode.timer.timeout.connect(self.update_plot)
            self.ComboBox_Mode.setItemData(3, Weiner_obj, Qt.UserRole)
            self.Change_mode(3)
            # print(f"shape of signal after creation :{self.modified_audio.shape}")
            # print(f"shape outputt {self.audio_data.shape}")
            amplitude,SR=self.Weiner_Orginal_Signals_data[num][0] ,self.Weiner_Orginal_Signals_data[num][1] 
            # print(f"shape the input shoulddd {amplitude.shape}")

            self.mode.signal.amplitude=amplitude
            # print(f"after corretionmn : {self.mode.signal.amplitude.shape}")
            self.spectrogram_widget1.plot_spectrogram(amplitude, SR )
            if self.Rec is not None :self.Widget_Signal_Input.removeItem(self.Rec)  


        # self.spectrogram_widget2.plot_spectrogram(self.mode.signal.amplitude, self.mode.signal.sample_rate )


    def play_noisy_signal(self,num):
            if self.Rec is not None :self.Widget_Signal_Input.removeItem(self.Rec)
            signal=self.Weiner_Noise[num][1]
            Weiner_obj=mode(signal , True)
            Weiner_obj.freq_slices=self.freq_tst
            self.mode=Weiner_obj 
            self.mode.timer.start()
            self.mode.timer.timeout.connect(self.update_plot)
            self.ComboBox_Mode.setItemData(3, Weiner_obj, Qt.UserRole)
            self.Change_mode(3)
            

            
    def iterative_wiener_filter(self, noisy_signal, noise_signal, fs, n_fft=1024, overlap=None, iterations=3, spectral_floor=0.1):
        if overlap is None:
            overlap = n_fft // 2

        if overlap >= n_fft:
            raise ValueError('noverlap must be less than nperseg.')

        f, t, noisy_stft = stft(noisy_signal, fs, nperseg=n_fft, noverlap=overlap)
        _, _, noise_stft = stft(noise_signal, fs, nperseg=n_fft, noverlap=overlap)

        noise_psd = np.mean(np.abs(noise_stft) ** 2, axis=-1, keepdims=True)
        filtered_stft = noisy_stft

        for _ in range(iterations):
            noisy_psd = np.abs(filtered_stft) ** 2
            wiener_filter = np.maximum(noisy_psd / (noisy_psd + noise_psd), spectral_floor)
            filtered_stft = wiener_filter * noisy_stft

        _, denoised_signal = istft(filtered_stft, fs, nperseg=n_fft, noverlap=overlap)
        return denoised_signal.ravel()
    

    def Calculate_Weiner_orginal_data(self):
        amplitude , sample_rate = librosa.load("Data/Weiner_Data/song_final_1.wav", sr=None)
        self.Weiner_Orginal_Signals_data[0]=[amplitude , sample_rate]
       
        amplitude , sample_rate = librosa.load("Data/Weiner_Data/song_final_2.wav" , sr= None)
        self.Weiner_Orginal_Signals_data[1]=[amplitude , sample_rate]
        
        amplitude , sample_rate = librosa.load("Data/Weiner_Data/song_final_3.wav" , sr= None)
        self.Weiner_Orginal_Signals_data[2]=[amplitude , sample_rate]
    
    def Select_Part(self):
        
        self.Rec=pg.RectROI([8, -0.5] , [3,0.5] ,pen='blue', movable=True, resizable=True )       
        self.Widget_Signal_Input.addItem(self.Rec)  



if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())