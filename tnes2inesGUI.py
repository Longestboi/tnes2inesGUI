#/usr/bin/env python3
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QPushButton, QFileDialog, QMessageBox
import sys
import ui
import zlib
import os

#
# A tool to extract PRG and CHR ROMs, FDS Bios, and FDS QD's from TNES ROM files, and to convert from TNES ROMs to INES ROMs 
#

def readFileMagic(file):
    file.seek(0, 0)
    byte = file.read(4)
    return byte

def readTNESHeader(file):
    file.seek(4, 0)
    byte = file.read(12)
    return byte

tnesRom = ''
TNESHeaderMinusMagic = ''

class TnesUIMain(QtWidgets.QMainWindow, ui.Ui_MainWindow):


    fileName = ''
    def __init__(self, parent=None):
        super(TnesUIMain, self).__init__(parent)
        self.setupUi(self)

        self.OpenRom.clicked.connect(self.openRomFile)
        self.TNEStoINES.clicked.connect(self.GUI_ConvToINES)
        self.ExtractQD.clicked.connect(self.GUI_ExtractQD)
        self.ExtractPRG.clicked.connect(self.GUI_ExtractPRGROM)
        self.ExtractCHR.clicked.connect(self.GUI_ExtractCHRROM)
        self.ExtractFDSBIOS.clicked.connect(self.GUI_ExtractFDSBIOS)

    def openRomFile(self):
        self.clearAllFields()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        global fileName
        fileName, _ = QFileDialog.getOpenFileName(self, "Open TNES Rom file", "","All Files(*)", options=options) # Types of openable files

        # Check if input is a TNES rom file if not, return
        global tnesRom
        tnesRom = open(fileName, 'rb')
        
        if (readFileMagic(tnesRom) != b'TNES'): # displays error if input file is not a TNES ROM
            fileName = ''
            errorDialog = QtWidgets.QMessageBox.warning(self, "Error!", "Input File is not a TNES ROM file.")
            return

        # Fill out rom info
        global TNESHeaderMinusMagic
        TNESHeaderMinusMagic = readTNESHeader(tnesRom)

        # Display Rom name in textbox
        self.DisplayRomName.insertHtml('<p style="color:grey">'+fileName+"</p>")
        self.fillOutAllInfo()

        return
        
    
    def clearAllFields(self):
        cleared = "N/A"
        global fileName
        fileName = '' # Clear the File Name
        self.DisplayRomName.setText('') # Clear text box
        global TNESHeaderMinusMagic
        TNESHeaderMinusMagic = '' # Clear the Header info
        #TNES
        self.Mapper_C.setText(cleared)
        self.PRGROMSize_C.setText(cleared)
        self.PRGROMCRC_C.setText(cleared)
        self.CHRROMSize_C.setText(cleared)
        self.CHRROMCRC_C.setText(cleared)
        self.WRAM_C.setText(cleared)
        self.Mirroring_C.setText(cleared)
        self.Battery_C.setText(cleared)
        #FDS
        self.FDSBIOSCRC_C.setText(cleared)
        self.FDSDiskCount_C.setText(cleared)
        self.FDSSidesPerDisk_C.setText(cleared)
    
    def fillOutAllInfo(self):
        tnesHeader = TNESHeader()
        extracter = TNESExtractor()

        if (tnesHeader.getMapper() != "FDS"):
            self.Mapper_C.setText(tnesHeader.getMapper())
            self.PRGROMSize_C.setText(str(tnesHeader.getPRGSize()))
            self.PRGROMCRC_C.setText(hex(zlib.crc32(extracter.extPRGRom(int(tnesHeader.getPRGSize()))))[2:])
            self.CHRROMSize_C.setText(str(tnesHeader.getCHRSize()))
            if (tnesHeader.getCHRSize() != "No CHR rom"): # Check if TNES ROM has a CHR ROM
                self.CHRROMCRC_C.setText(hex(zlib.crc32(extracter.extCHRRom(int(tnesHeader.getPRGSize()), int(tnesHeader.getCHRSize()))))[2:])
            self.WRAM_C.setText(tnesHeader.hasWRAM())
            self.Mirroring_C.setText(tnesHeader.getMirroring())
            self.Battery_C.setText(tnesHeader.hasBattery())
        else:
            self.FDSBIOSCRC_C.setText(tnesHeader.getFDSBioscrc32(tnesRom))
            self.FDSDiskCount_C.setText(tnesHeader.getDiskCount())
            self.FDSSidesPerDisk_C.setText(tnesHeader.getSidePerDiskCount())

    def GUI_ExtractPRGROM(self):
        tnesHeader = TNESHeader()
        extracter = TNESExtractor()
        if (tnesHeader.getMapper() == "FDS"): # Error out if Tnes contains FDS file
            errorDialog = QtWidgets.QMessageBox.warning(self, "Error!", "Cannot extract PRG ROM from FDS TNES file.")
            return
        else:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog

            global fileName # Grab file path and strip to original filename
            PRGROMout, _ = QFileDialog.getSaveFileName(self, "Save PRG Rom file", os.path.split(fileName)[1]+"-PRG.bin",".bin", options=options)
            
            if PRGROMout: # check if PRGROMout var was set
                extracter.saveToFile(PRGROMout, extracter.extPRGRom(tnesHeader.getPRGSize()))
    
    def GUI_ExtractCHRROM(self):
        tnesHeader = TNESHeader()
        extracter = TNESExtractor()
        if (tnesHeader.getMapper() == "FDS"): # Error out if TNES contains FDS file
            errorDialog = QtWidgets.QMessageBox.warning(self, "Error!", "Cannot extract CHR ROM from FDS TNES file.")
            return
        if (tnesHeader.getCHRSize() == "No CHR rom"): # Error if TNES does not have any CHR ROM
            errorDialog = QtWidgets.QMessageBox.warning(self, "Error!", "TNES ROM does not have any CHR ROM.")
            return
        else:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog

            global fileName # Grab file path and strip to original filename
            CHRROMout, _ = QFileDialog.getSaveFileName(self, "Save CHR Rom file", os.path.split(fileName)[1]+"-CHR.bin",".bin", options=options)
            
            if CHRROMout: # check if CHRROMout var was set
                extracter.saveToFile(CHRROMout, extracter.extCHRRom(tnesHeader.getPRGSize(), tnesHeader.getCHRSize()))
   
    def GUI_ExtractFDSBIOS(self):
        tnesHeader = TNESHeader()
        extracter = TNESExtractor()
        if (tnesHeader.getMapper() != "FDS"):
            errorDialog = QtWidgets.QMessageBox.warning(self, "Error!", "TNES file does not contain a FDS BIOS.")
            return
        else:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            crc32 = tnesHeader.getFDSBioscrc32(tnesRom)
            FDSBIOSout, _ = QFileDialog.getSaveFileName(self, "Save FDS BIOS", crc32+"-fds.bin", ".bin", options=options)
            if FDSBIOSout:
                extracter.dumpFDSBios(tnesRom, FDSBIOSout)
    
    def GUI_ExtractQD(self):
        tnesHeader = TNESHeader()
        extracter = TNESExtractor()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        global tnesRom
        if (tnesHeader.getMapper() == "FDS"):
            FDSQDOut, _ = QFileDialog.getSaveFileName(self, "Save QD File", os.path.split(fileName)[1]+".qd", ".qd", options=options)
            if FDSQDOut:
                extracter.extQD(tnesRom, FDSQDOut)

    def GUI_ConvToINES(self):
        tnesHeader = TNESHeader()
        extracter = TNESExtractor()
        tnesConv = TNESConv()
        if (tnesHeader.getMapper() == "FDS"):
            errorDialog = QtWidgets.QMessageBox.warning(self, "Error!", "Cannot convert FDS TNES to INES.")
            return
        
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        global fileName
        INESFileName = os.path.split(fileName)[1]+".nes"
        INESout, _ = QFileDialog.getSaveFileName(self, "Save NES ROM", INESFileName, ".nes", options=options)
        if INESout:
            conv = open(INESout, "wb")
            conv.write(bytes(tnesConv.retINESMagic().encode("utf-8")))
            conv.seek(len(tnesConv.retINESMagic()))
            #prg size
            conv.write(tnesConv.retSizeOfRomMultipleKB(tnesHeader.getPRGSize(), "prg"))
            #chr size
            conv.write(tnesConv.retSizeOfRomMultipleKB(tnesHeader.getCHRSize(), "chr"))

            #flag 6 - mapper, mirroring, battery
            flag6 = [0, 0, 0, 0]

            #handle the mappers
            mapperList = {
                1: "0000",#NROM
                2: "0001",#SxROM
                3: "1001",#PNROM
                4: "0100",#TxROM
                5: "1010",#FxROM
                6: "0101",#ExROM
                7: "0010",#UxROM
                8: "0011",#CNROM
                9: "0111"}#AxROM

            a = int(tnesHeader.getMapper(True) + 1)
            lowerNyb = mapperList[a]

            #handle if the rom uses a battery backed save
            if (tnesHeader.hasBattery() == "Yes"):
                flag6[2] = 1
            else:
                flag6[2] = 0

            if (tnesHeader.getMirroring() == "Mapper Controlled" or tnesHeader.getMirroring() == "Horizontal"):
                flag6[3] = 0
            elif (tnesHeader.getMirroring() == "Vertical"):
                flag6[3] = 1

            #conv list to string
            flag6String = ''.join(str(e) for e in flag6)

            full = int(lowerNyb + flag6String, 2).to_bytes(1, byteorder="big")

            conv.write(full)
            conv.write(bytes(9))
            conv.write(extracter.extPRGRom(int(tnesHeader.getPRGSize())))
            if (tnesHeader.getCHRSize() != "No CHR rom"):
                conv.write(extracter.extCHRRom(int(tnesHeader.getPRGSize()), int(tnesHeader.getCHRSize())))

            conv.close()



class TNESHeader: 

    def getMapper(self, outputNumber=False):
        mapper = TNESHeaderMinusMagic[0]
        TNESMappers = ["NROM", "SxROM", "PNROM", "TxROM", "FxROM", "ExROM", "UxROM", "CNROM", "AxROM", "FDS"] 
        if (mapper == 9):
            a = 8
        if (mapper == 100):
            a = 9
        else:
            a = mapper
        if (outputNumber == True):
            return a
        return TNESMappers[a]
    
    def getPRGSize(self):
        prgMultiple = TNESHeaderMinusMagic[1]
        if (prgMultiple == 0):
            return "No PRG rom"
        else:
            prgRomSize = prgMultiple * 8192
            return prgRomSize

    def getCHRSize(self):
        chrMultiple = TNESHeaderMinusMagic[2]
        if (chrMultiple == 0):
            return "No CHR rom"
        else:
            chrRomSize = chrMultiple * 8192
            return chrRomSize 

    def hasWRAM(self):
        boolean = TNESHeaderMinusMagic[3]
        if (boolean == 0):
            return "No"
        if (boolean == 1):
            return "Yes"
        else:
            return "Couldn't check if game uses WRAM"

    def getMirroring(self):
        mirror = TNESHeaderMinusMagic[4]
        if (mirror == 0):
            return "Mapper controlled"
        if (mirror == 1):
            return "Horizontal"
        if (mirror == 2):
            return "Vertical"
        else:
            return "Couldn't find mirroring type"

    def hasBattery(self):
        bat = TNESHeaderMinusMagic[5]
        if (bat == 0):
            return "No"
        if (bat == 1):
            return "Yes"
        else:
            return "Couldn't find if game uses a battery"

    def getFDSBioscrc32(self, file):
        file.seek(16, 0)
        biosCRC32 = zlib.crc32(file.read(8192))
        biosCRC32 = str(hex(biosCRC32)[2:])
        return biosCRC32

    def getSidePerDiskCount(self):
        sides = TNESHeaderMinusMagic[6]
        mod = sides / 2
        if (((mod % 2) == 0)):
            sides = mod
        return str(int(sides))

    def getDiskCount(self):
        sides = int(self.getSidePerDiskCount())
        if (sides == 1):
            disks = 1.0
        if ((sides % 2) == 0):
            disks = sides / 2
        return str(disks)[:-2]

class TNESExtractor:
    def extPRGRom(self, PRGSize):
        #Seek to constant prg rom location
        tnesRom.seek(16, 0)

        return tnesRom.read(PRGSize)
        
    def extCHRRom(self, PRGSize, CHRSize):
        #Seek to variable chr rom location
        chrseek = PRGSize + 16
        tnesRom.seek(chrseek, 0)
        
        return tnesRom.read(CHRSize)
        
    def dumpFDSBios(self, file, fileName):
        bios = open(fileName, 'wb')
        file.seek(16, 0)
        bios.write(file.read(8192))
        bios.close
    
    def extQD(self, file, fileName):
        qd = open(fileName, 'wb')
        file.seek(8208, 0)
        qd.write(file.read())
        qd.close()

    def saveToFile(self, fileName, inFile):
        dump = open(fileName, 'wb')
        dump.write(inFile)
        dump.close()

class TNESConv:
    def retINESMagic(self):
        return "NES\x1A"

    def retSizeOfRomMultipleKB(self, ROMSize, PRGorCHR):
        if (ROMSize == "No CHR rom" or ROMSize == "No PRG rom"):
            return bytes(1)
        if (PRGorCHR == "prg" or PRGorCHR == "PRG"):
            size = int(int(ROMSize) / 16000)
        elif (PRGorCHR == "chr" or PRGorCHR == "CHR"):
            size = int(int(ROMSize) / 8000)
        return size.to_bytes(1, byteorder="big")

def main():
    app = QApplication(sys.argv)    
    form = TnesUIMain()
    form.show()
    app.exec_()

if __name__ == '__main__':
    main()
