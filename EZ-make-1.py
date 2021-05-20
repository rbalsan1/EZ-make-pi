from guizero import App, TextBox, PushButton, Text, Box, Combo, Drawing, Window
import os
import time
import json
import array
import board
import busio
import digitalio
import max6675
#set up globals
sgraph = 0
plot = 0
#tempValue = 0
palette = ["black","green","blue","red","yellow"]
PROFILE_SIZE = 2            # plot thickness
GRID_SIZE = 2
GRID_STYLE = 3
TEMP_SIZE = 2
AXIS_SIZE = 2 
BACKGROUND_COLOR = 0
PROFILE_COLOR = 1
GRID_COLOR = 2
TEMP_COLOR = 3
AXIS_COLOR = 4
WIDTH = 400
HEIGHT = 400 
GXSTART = 100
GYSTART = 80
GWIDTH = WIDTH - GXSTART
GHEIGHT = HEIGHT - GYSTART
"""program setup"""
#init the gui
app = App(bg = "black", width = 800, height = 480)
controls_box = Box(app, width="fill", align="left")
#make title
indicatorBox = Box(app, width="fill", align = "top")
Title =Text(indicatorBox, text = "EZ Make Oven Controller", font = "Times New Roman", size = 16, color = "white", align = "left")
message =  Text(app, text = "Getting started", font = "Times New Roman", size = 14, color = "white", align = "top")
indicator= Drawing(indicatorBox,25,25, align = "right")
indicator.oval(0, 00, 24, 24, color="black", outline=True, outline_color="white")
#define the display panel
alloy_label = Text(controls_box, text="Alloy:", size = 14, color = "blue")
alloy_display = Text(controls_box, text = "", size = 12, color = "white")
profile_label = Text(controls_box, text="Profile:", size = 14, color = "blue")
profile_display = Text(controls_box, text="", size = 12, color = "white")
time_label = Text(controls_box, text="Time:", size = 14, color = "blue")
time_dispay = Text(controls_box, text=0, size = 16, color = "white")
temp_label = Text(controls_box, text="Temp (C):", size = 14, color = "blue")
temp_display = Text(controls_box, text=0, size = 16, color = "white")
last_temp = 0
last_state = "ready"
last_control = False
second_timer = time.monotonic()
timer = time.monotonic()
def temp_update():
    oven.read_temp(oven.sensor)
    oven.beep.refresh()  # this allows beeps- we can't have beeps holding up the works
#end my original code and begin the code from adafruit

    try:
        oven_temp = int(oven.temperature)
    except runtimeError:
        oven_temp = 32  # testing
        oven.sensor_status = False
        message.value = "Bad/missing temp sensor"
    global last_control
    global last_temp
    global last_state
    global timer
    global second_timer
    global timediff
    global sgraph
    if oven.control != last_control:
        last_control = oven.control
        if oven.control:
            indicator.clear()
            indicator.oval(0, 00, 24, 24, color="red", outline=True, outline_color="white")
        else:
            indicator.clear()
            indicator.oval(0, 00, 24, 24, color="black", outline=True, outline_color="white")  
#Button stuff obsolete
    status = ""
    last_status = ""
    if oven.sensor_status:
        if oven.state == "ready":
            status = "Ready"
            if last_state != "ready":
                oven.beep.refresh()
                oven.reset()
                #draw_profile(sgraph, oven.sprofile)#don't think I can draw profile evry time (very memory )
                time_dispay.value = time.strftime("%H:%M:%S",time.gmtime(0))
            if button.text != "Start":
                button.text = "Start"
        if oven.state == "start":
            status = "Starting"
            if last_state != "start":
                timer = time.monotonic()
        if oven.state == "preheat":
            if last_state != "preheat":
                timer = time.monotonic()  # reset timer when preheat starts
            status = "Preheat"
        if oven.state == "soak":
            status = "Soak"
        if oven.state == "reflow":
            status = "Reflow"
        if oven.state == "cool" or oven.state == "wait":
            status = "Cool Down, Open Door"
        if last_status != status:
            message.value = status
            last_status = status
 
        if oven_temp != last_temp and oven.sensor_status:
            last_temp = oven_temp
            temp_display.value = str(oven_temp)
        # update once per second when oven is active
        if oven.state != "ready" and time.monotonic() - second_timer >= 1.0:
            second_timer = time.monotonic()
            oven.check_state()
            if oven.state == "preheat" and last_state != "preheat":
                timer = time.monotonic()  # reset timer at start of preheat
            timediff = int(time.monotonic() - timer)
            time_dispay.value = time.strftime("%H:%M:%S",time.gmtime(timediff))
            print(oven.state)
            if oven_temp >= 50:
                sgraph.draw_graph_point(
                    int(timediff), oven_temp, size=TEMP_SIZE, color=TEMP_COLOR
                )
 
        last_state = oven.state
temp_display.repeat(250,temp_update)
    #define the control panel
#have to step through the profiles directory to pull out all of the 
def getProfileList():#this should be part o an init
    f = []
    try:
        for (dirpath, dirnames, filenames) in os.walk("./profiles/"):
            f.extend(filenames)
            break
    except:
        return f
    return f
fileLabel = Text(controls_box, text="From File:", size = 14, color = "blue")
def file_display_command(selected_file):
    with open("config.json", mode="r") as fpr:
        config = json.load(fpr)
        fpr.close()
    config["profile"] = selected_file[0:len(selected_file)-5]
    with open("config.json", mode="w") as fpr:
        json.dump(config,fpr)
        fpr.close()
    with open("profiles/" + config["profile"] + ".json", mode="r") as fpr:
        oven.sprofile = json.load(fpr)
        fpr.close()
    loadPlot()
    # print("plot loaded")
file_box_1 = Box(controls_box)

fileDisplay = Combo(file_box_1, options=getProfileList(),command= file_display_command, align = "left")
fileDisplay.size = 24
fileDisplay.bg = "white"
def editor_launcher():

    def copy():
        copy_window = Window(json_editor_window,title = "create a copy")
        copy_window.show(wait=True)
        Text(copy_window, text = "Name of copy :")
        file_name = TextBox(copy_window, text = file_display.value, enabled = True, width = "fill")
        file_name.when_left_button_released = text_click
        def complete_copy():
            destination = file_name.value
            save(0,destination)
            copy_window.destroy()
        ok_button = PushButton(copy_window, text = "OK" ,command = complete_copy)
        cancel_button = PushButton(copy_window, text = "cancel", command = copy_window.destroy)
    def text_click(box):
        key_pad.show(wait=True)
        key_pad.focus()
        text_input.value = box.widget.value
        make_keyboard("num",box)
    def save(is_it_from_save_butt,save_new_file):
        global json_file
        for values in json_file:
            if values=="stages":
                for subtitle in json_file[values]:
                    coords = []
                    for coord in json_file[values][subtitle]:
                        entry = coord.value
                        coords.append(int(entry))
                    json_file[values][subtitle] = coords
            elif values=="profile":
                list_of_coords = []
                for subtitle in json_file[values]:
                    coords = []
                    for coord in subtitle:
                        entry = coord.value
                        coords.append(int(entry))
                    list_of_coords.append(coords)
                json_file[values] = list_of_coords
            elif values=="temp_range" or values == "time_range":
                coords = []
                for coord in json_file[values]:
                    entry =coord.value
                    coords.append(int(entry))
                json_file[values]=coords
            else:
                entry = json_file[values].value
                json_file[values] = entry 
        if is_it_from_save_butt == True:
            with open("profiles/" +file_display.value, mode="w") as fpr:
                json.dump(json_file,fpr)
                fpr.close()
            file_load(file_display.value)
        else:
            with open("profiles/" +save_new_file, mode="w") as fpr:
                json.dump(json_file,fpr)
                fpr.close()
            file_load(save_new_file)
            file_display.append(save_new_file)
            file_display.value = save_new_file
    def get_profile_list():
        f = []
        try:
            for (dirpath, dirnames, filenames) in os.walk("./profiles/"):
                f.extend(filenames)
                break
        except:
            return f
        return f
    def file_load(selected_file):
        global json_file
        while len(box2.children)>0:
            for child in box2.children:
                child.destroy()
        with open("profiles/" + selected_file, mode="r") as fpr:
            json_file = json.load(fpr)
            fpr.close()
        row=3
        for values in json_file:
            if values=="stages":
                row = 1
                entry=Text(box2,text=values,color="blue", grid = [3,row])
                entry = Text(box2,text="Time",color="yellow", grid = [5,row])
                entry = Text(box2,text="Temperature",color="yellow", grid = [6,row])
                row+=1
                for subtitle in json_file[values]:
                    entry = Text(box2,text=subtitle, color="yellow", grid = [4, row])
                    x=5
                    coords = []
                    for coord in json_file[values][subtitle]:
                        entry = TextBox(box2,coord,grid = [x,row])
                        entry.when_left_button_released = text_click
                        entry.bg = "white"
                        coords.append(entry)
                        x+=1
                    json_file[values][subtitle] = coords
                    row+=1
            elif values=="profile":
                row = 1
                entry = Text(box2,text=values,color="blue", grid = [7,row])
                entry = Text(box2,text="Time",color="yellow", grid = [8,row])
                entry = Text(box2,text="Temperature",color="yellow", grid = [9,row])
                row+=1
                list_of_coords = []
                for subtitle in json_file[values]:
                    x=8
                    coords = []
                    for coord in subtitle:
                        entry = TextBox(box2,coord,grid = [x,row])
                        entry.when_left_button_released=text_click
                        entry.bg = "white"
                        coords.append(entry)
                        x+=1
                    row+=1
                    list_of_coords.append(coords)
                def add_row():
                    global add_button
                    global subtract_button
                    global json_file
                    row=2+len(json_file["profile"])
                    x=8
                    coords = []
                    for coord in range(0,2):
                        entry = TextBox(box2,coord,grid = [x,row])
                        entry.when_left_button_released=text_click
                        entry.bg = "white"
                        coords.append(entry)
                        x+=1
                    row+=1
                    add_button.destroy()
                    subtract_button.destroy()
                    add_button = PushButton(box2,text = "+",grid=[8,row],command = add_row)
                    add_button.bg="white"
                    subtract_button = PushButton(box2,text = "-",grid=[9,row], command=subtract_row)
                    subtract_button.bg="white"
                    json_file["profile"].append(coords)
                def subtract_row():
                    global add_button
                    global subtract_button
                    global json_file
                    row=len(json_file["profile"])-1
                    x=8
                    coords = []
                    for coord in json_file["profile"][row]:
                        coord.destroy()
                        x+=1
                    json_file["profile"].pop()
                    row = len(json_file["profile"])+2
                    add_button.destroy()
                    subtract_button.destroy()
                    add_button = PushButton(box2,text = "+",grid=[8,row],command = add_row)
                    add_button.bg="white"
                    subtract_button = PushButton(box2,text = "-",grid=[9,row], command = subtract_row)
                    subtract_button.bg="white"

                global add_button
                global subtract_button
                add_button = PushButton(box2,text = "+",grid=[8,row],command = add_row)
                add_button.bg="white"
                subtract_button = PushButton(box2,text = "-",grid=[9,row],  command = subtract_row)
                subtract_button.bg="white"
                json_file[values] = list_of_coords
            elif values=="temp_range" or values == "time_range":
                entry = Text(box2,text=values,color="blue", grid = [0,row])
                entry = Text(box2,text="min",color="yellow", grid = [1,row])
                entry = Text(box2,text="max",color="yellow", grid = [2,row])
                row+=1
                x=1
                coords = []
                for coord in json_file[values]:
                    entry = TextBox(box2,coord,grid = [x,row])
                    entry.when_left_button_released=text_click
                    entry.bg = "white"
                    coords.append(entry)
                    x+=1
                json_file[values]=coords
                row+=1

            else:
                entry = Text(box2,text=values, color = "blue", grid = [0,row])
                entry = TextBox(box2,json_file[values], grid = [1,row])
                entry.when_left_button_released = text_click
                entry.bg = "white"
                json_file[values] = entry 
                row+=1

        

    json_editor_window = Window(app,bg = "black", width = 800, height = 480, layout = "auto")
    Text(json_editor_window, text="Profile Editor", color = "blue", size = 15)
    box3 = Box(json_editor_window, layout = "grid")
    file_display = Combo(box3, options=get_profile_list(), command = file_load, grid = [0,0] )
    def delete_profile():
        global file_display
        os.remove("profiles/" + file_display.value)
        file_display.destroy()
        file_display = Combo(box3, options=get_profile_list(), command = file_load, grid = [0,0] )
        file_display.size = 24
        file_display.bg = "white"
        file_load(file_display.value)
    delete_file = PushButton(box3, grid = [1,0], command = delete_profile, text = "delete")
    delete_file.bg = "white"
    file_display.size = 24
    file_display.bg = "white"
    box1 = Box(json_editor_window)
    copy_button = PushButton(box1, command=copy, text="copy", align = "left")
    copy_button.bg="white"
    save_button = PushButton(box1, command=save, text="save", enabled=True, align = "left",args = [True,0])
    save_button.bg = "white"
    box2= Box(json_editor_window,layout = "grid")
    # json_editor_window.set_full_screen()
    key_pad = Window(json_editor_window,title = "key_pad",width = 800, height = 480,)
    # key_pad.set_full_screen()
    text_input = TextBox(key_pad,width = "fill")
    key_pad.hide()
    def make_keyboard(key_board,field=0):
        def enter_text(text):
            old_string = text_input.value
            new_string =  old_string + str(text)
            text_input.value = new_string
        key_box = Box(key_pad, layout="grid")
        def switch_keyboard(argument):
            # print("switch")
            key_box.destroy()
            cancel_button.destroy()
            ok_button.destroy()
            make_keyboard(argument,field)
        if key_board == "num":
            for button in range(0,10):
                key_button = PushButton(key_box,text=str(button),padx = 16,grid=[button % 3,button//3+1], command = enter_text, args =[button])
                key_button.bg="white"
            def back_space():
                old_string = text_input.value
                new_string =  old_string[0:len(old_string)-1] 
                text_input.value = new_string
            key_button = PushButton(key_box,text="<X|",grid=[11 % 3,11//3+1], command = back_space)
            key_button.bg="white"
            key_button = PushButton(key_box,text="abc",grid=[10 % 3,10//3+1], command = switch_keyboard, args = ["alph"])
            key_button.bg="white"
        elif key_board == "alph":
            row = 0
            characters = ["qwertyuiop[]","asdfghjkl;'","zxcvbnm,./"," "]
            for string in characters:
                column = 0
                if len(string)==1:
                    button = string[0]
                    key_button = PushButton(key_box,text=str(button), padx = 100,grid=[column,row,12,1], command = enter_text, args =[button])
                    key_button.bg="white"
                else:    
                    for button in string:
                        key_button = PushButton(key_box,text=str(button),padx = 16,grid=[column,row], command = enter_text, args =[button])
                        key_button.bg="white"
                        column +=1
                    if row == len(characters)-2:
                        button = PushButton(key_box,text="shift",padx = 16,grid=[column,row], command = switch_keyboard, args =["ALPH"])
                row+=1
            def back_space():
                old_string = text_input.value
                new_string =  old_string[0:len(old_string)-1] 
                text_input.value = new_string
            key_button = PushButton(key_box,text="<X|",grid=[11 % 3,11//3+1], command = back_space)
            key_button.bg="white"
            key_button = PushButton(key_box,text="123",grid=[10 % 3,10//3+1], command = switch_keyboard, args = ["num"])
            key_button.bg="white"
        elif key_board == "ALPH":
            row = 0
            characters = ["QWERTYUIOP{}","ASDFGHJKL:'","ZXCVBNM<>?"," "]
            for string in characters:
                column = 0
                if len(string)==1:
                    button = string[0]
                    key_button = PushButton(key_box,text=str(button), padx = 100,grid=[column,row,12,1], command = enter_text, args =[button])
                    key_button.bg="white"
                else:    
                    for button in string:
                        key_button = PushButton(key_box,text=str(button),padx = 16,grid=[column,row], command = enter_text, args =[button])
                        key_button.bg="white"
                        column +=1
                    if row == len(characters)-2:
                        button = PushButton(key_box,text="shift",padx = 16,grid=[column,row], command = switch_keyboard, args =["alph"])
                row+=1
            def back_space():
                old_string = text_input.value
                new_string =  old_string[0:len(old_string)-1] 
                text_input.value = new_string
            key_button = PushButton(key_box,text="<X|",grid=[11 % 3,11//3+1], command = back_space)
            key_button.bg="white"
            key_button = PushButton(key_box,text="123",grid=[10 % 3,10//3+1], command = switch_keyboard,args = ["num"])
            key_button.bg="white"
        def write_text(textbox):
            textbox.value = text_input.value
            key_pad.hide()
            cancel_button.destroy()
            ok_button.destroy()
            key_box.destroy()
        def cancel():
            key_pad.hide()
            cancel_button.destroy()
            ok_button.destroy()
            key_box.destroy()
        ok_button=PushButton(key_pad, text = "ok", command = write_text, args = [field.widget])
        cancel_button=PushButton(key_pad, text = "cancel", command = cancel)
        key_pad.when_closed = cancel
        
    file_load(file_display.value)    
    json_editor_window.display()

profile_editor_button = PushButton(file_box_1, text = "edit", command = editor_launcher, align = "left")
profile_editor_button.bg = "white"
def abort():
    message.value = "aborting. . ."
    time_dispay.value = 0
    loadPlot()
    fileDisplay.enable()
    button.text = "start"
    message.value = "Ready"
    print("aborting") 

def buttonPush():
    if oven.state == "ready":
        button.text = "Stop"
        oven.set_state("start")
        fileDisplay.disable()
    else:
        # abort operation
        message.value = "Wait"
        button.text = "Wait"
        oven.reset()
        oven.set_state("wait")
        abort()

button = PushButton(controls_box, command=buttonPush , text = "start")
button.bg = "white"
plot = Drawing(app,GWIDTH,GHEIGHT, align="bottom")
"""begin oven control class"""
class ReflowOvenControl(object):#should probably rename
    states = ("wait", "ready", "start", "preheat", "soak", "reflow", "cool")#class variable
 
    def __init__(self, pin):
        try:
            with open("config.json", mode="r") as fpr:#try and except here because there is a changeable file system on the pi
                self.config = json.load(fpr)
                fpr.close()
        except FileNotFoundError:
            message.value = "config load error"
            self.error = 1#not good but better
            print("could not open config file")
        try:
            with open("profiles/" + self.config["profile"] + ".json", mode="r") as fpr:
                self.sprofile = json.load(fpr)
                fpr.close()
                self.error = 0#not good but better
            message.value = "Getting started"
            fileDisplay.value =  self.config["profile"] + ".json"

        except FileNotFoundError:
            message.value = "profile load error"
            self.error = 1#not good but better
        self.oven = digitalio.DigitalInOut(pin)
        self.oven.direction = digitalio.Direction.OUTPUT
        spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
        cs = digitalio.DigitalInOut(board.D2)
        self.sensor_status = False
        try:
            self.sensor = max6675.MAX6675(spi, cs)
            self.read_temp(self.sensor)
            self.ontemp = self.temperature
            self.offtemp = self.ontemp
            self.sensor_status = True
        except RuntimeError:
            print("temperature sensor not available")
        self.control = False
        self.reset()
        self.beep = Beep()
        self.set_state("ready")
        if self.sensor_status:
            if self.temperature >= 50:
                self.last_state = "wait"
                self.set_state("wait")
    def read_temp(self,sensor):
        self.temperature = sensor.temperature
    def reset(self):
        self.ontime = 0
        self.offtime = 0
        self.enable(False)
        self.reflow_start = 0
 
    def get_profile_temp(self, seconds):
        x1 = self.sprofile["profile"][0][0]
        y1 = self.sprofile["profile"][0][1]
        for point in self.sprofile["profile"]:
            x2 = point[0]
            y2 = point[1]
            if x1 <= seconds < x2:
                temp = y1 + (y2 - y1) * (seconds - x1) // (x2 - x1)
                return temp
            x1 = x2
            y1 = y2
        return 0
 
    def set_state(self, state):
        self.state = state
        self.check_state()
        self.last_state = state
 
    # pylint: disable=too-many-branches, too-many-statements
    def check_state(self):
        global sgraph
        try:
            temp = self.temperature
        except runtimeError:
            temp = 32  # sensor not available, use 32 for testing
            self.sensor_status = False
            # message.value = "Temperature sensor missing"
        self.beep.refresh()
        if self.state == "wait":
            self.enable(False)
            if self.state != self.last_state:
                # change in status, time for a beep!
                self.beep.play(0.1)
            if temp < 35:
                self.set_state("ready")
                oven.reset()
                draw_profile(sgraph, self.sprofile)
                time_dispay.value = time.strftime("%H:%M:%S",time.gmtime(0))
 
        if self.state == "ready":
            self.enable(False)
        if self.state == "start" and temp >= 50:
            self.set_state("preheat")
        if self.state == "start":
            message.value = "Starting"
            self.enable(True)
        if self.state == "preheat" and temp >= self.sprofile["stages"]["soak"][1]:
            self.set_state("soak")
        if self.state == "preheat":
            message.value = "Preheat"
        if self.state == "soak" and temp >= self.sprofile["stages"]["reflow"][1]:
            self.set_state("reflow")
        if self.state == "soak":
            message.value = "Soak"
        if (
            self.state == "reflow"
            and temp >= self.sprofile["stages"]["cool"][1]
            and self.reflow_start > 0
            and (
                time.monotonic() - self.reflow_start
                >= self.sprofile["stages"]["cool"][0]
                - self.sprofile["stages"]["reflow"][0]
            )
        ):
            self.set_state("cool")
            self.beep.play(5)
        if self.state == "reflow":
            message.value = "Reflow"
            if self.last_state != "reflow":
                self.reflow_start = time.monotonic()
        if self.state == "cool":
            self.enable(False)
            message.value = "Cool Down, Open Door"
 
        if self.state in ("start", "preheat", "soak", "reflow"):
            if self.state != self.last_state:
                # change in status, time for a beep!
                self.beep.play(0.1)
            # oven temp control here
            # check range of calibration to catch any humps in the graph
            checktime = 0
            checktimemax = self.config["calibrate_seconds"]
            checkoven = False
            if not self.control:
                checktimemax = max(
                    0,
                    self.config["calibrate_seconds"]
                    - (time.monotonic() - self.offtime),
                )
            while checktime <= checktimemax:
                global timediff
                check_temp = self.get_profile_temp(int(timediff + checktime))
                if (
                    temp + self.config["calibrate_temp"] * checktime / checktimemax
                    < check_temp
                ):
                    checkoven = True
                    break
                checktime += 5
            if not checkoven:
                # hold oven temperature
                if (
                    self.state in ("start", "preheat", "soak")
                    and self.offtemp > self.temperature
                ):
                    checkoven = True
            self.enable(checkoven)
 
    # turn oven on or off
    def enable(self, enable):
        try:
            self.oven.value = enable
            self.control = enable
            if enable:
                self.offtime = 0
                self.ontime = time.monotonic()
                self.ontemp = self.temperature
                print("oven on")
            else:
                self.offtime = time.monotonic()
                self.ontime = 0
                self.offtemp = self.temperature
                print("oven off")
        except runtimeError:
            # bad sensor
            pass

""" The graph class is being used to draw a graph"""
class Graph(object):
    def __init__(self):
        self.xmin = 0
        self.xmax = 720  # graph up to 12 minutes
        self.ymin = 0
        self.ymax = 240
        self.xstart = 0
        self.ystart = 0
        self.width = GWIDTH
        self.height = GHEIGHT
 
    def draw_line(self, x1, y1, x2, y2, size=PROFILE_SIZE, color=1, style=1):
        x1p = (self.xstart + self.width * (x1 - self.xmin)
               // (self.xmax - self.xmin))
        y1p = (self.ystart + int(self.height * (y1 - self.ymin)
                                 / (self.ymax - self.ymin)))
        x2p = (self.xstart + self.width * (x2 - self.xmin) //
               (self.xmax - self.xmin))
        y2p = (self.ystart + int(self.height * (y2 - self.ymin) /
                                 (self.ymax - self.ymin)))
        if (max(x1p, x2p) - min(x1p, x2p)) > (max(y1p, y2p) - min(y1p, y2p)):
            for xx in range(min(x1p, x2p), max(x1p, x2p)):
                if x2p != x1p:
                    yy = y1p + (y2p - y1p) * (xx - x1p) // (x2p - x1p)
                    if style == 2:
                        if xx % 2 == 0:
                            self.draw_point(xx, yy, size, color)
                    elif style == 3:
                        if xx % 8 == 0:
                            self.draw_point(xx, yy, size, color)
                    elif style == 4:
                        if xx % 12 == 0:
                            self.draw_point(xx, yy, size, color)
                    else:
                        plot.line(x1p, GHEIGHT - y1p, x2p, GHEIGHT - y2p, color=palette[color], width=size)
                        break
        else:
            for yy in range(min(y1p, y2p), max(y1p, y2p)):
                if y2p != y1p:
                    xx = x1p + (x2p - x1p) * (yy - y1p) // (y2p - y1p)
                    if style == 2:
                        if yy % 2 == 0:
                            self.draw_point(xx, yy, size, color)
                    elif style == 3:
                        if yy % 8 == 0:
                            self.draw_point(xx, yy, size, color)
                    elif style == 4:
                        if yy % 12 == 0:
                            self.draw_point(xx, yy, size, color)
                    else:
                        plot.line(x1p, GHEIGHT - y1p, x2p, GHEIGHT - y2p, color=palette[color], width=size) 
    def draw_graph_point(self, x, y, size=PROFILE_SIZE, color=1):
        """ draw point using graph coordinates """
        # wrap around graph point when x goes out of bounds
        x = (x - self.xmin) % (self.xmax - self.xmin) + self.xmin
        xx = (self.xstart + self.width * (x - self.xmin)
              // (self.xmax - self.xmin))
        yy = (self.ystart + int(self.height * (y - self.ymin)
                                / (self.ymax - self.ymin)))
        #print("graph point:", x, y, xx, yy)
        self.draw_point(xx, max(0 + size, yy), size, color)
 
    def draw_point(self, x, y, size=PROFILE_SIZE, color=1):
        """Draw data point on to the plot bitmap at (x,y)."""
        if y is None:
            return
        offset = size // 2
        xx = x-offset
        # for xx in range(x-offset, x+offset+1):
        if xx in range(self.xstart, self.xstart + self.width):
            yy = y-offset
                # for yy in range(y-offset, y+offset+1):
            if yy in range(self.ystart, self.ystart + self.height):
                try:
                    yy = GHEIGHT - yy
                    plot.rectangle(xx, yy, xx+size, yy+size, color = palette[color])#use size here to adjust rectangle size
                    # print("point")
                except IndexError:
                    pass
"""this ends the graph class"""
"""sensor class"""
"""this should draw the graph and the profile of heating"""
class Beep(object):
    def __init__(self):
        self.pin = digitalio.DigitalInOut(board.D17)
        self.pin.direction = digitalio.Direction.OUTPUT
        self.pin.value = False
        self.start = time.monotonic()
        self.duration = 0
# pylint: disable=protected-access
    def play(self, duration=0.250):
        if not self.pin.value:
            self.pin.value = True
            self.start = time.monotonic()
            self.duration = duration
 
    def stop(self):
        self.duration = 0
        self.pin.value = False
 
    def refresh(self):
        if time.monotonic() - self.start >= self.duration:
            self.stop()
timediff = 0
oven =  ReflowOvenControl(board.D4)
def loadPlot():#this is going to have to take an argument to work properly-explicitly a file name
    plot.clear()
    #create an oven object from the class takes the pin that controls the relay
    #these
    global oven
    if oven.error == 0:
    #create a graph instance which creates the Drawing object
        global sgraph
        sgraph = Graph()#global
    #set up the graph based on the initial parameters
        sgraph.xstart = 0
        sgraph.ystart = 0
        sgraph.width = GWIDTH  # is set for the gui manually
        sgraph.height = GHEIGHT  # is set for the gui manually
        sgraph.xmin = oven.sprofile["time_range"][0]
        sgraph.xmax = oven.sprofile["time_range"][1]
        sgraph.ymin = oven.sprofile["temp_range"][0]
        sgraph.ymax = oven.sprofile["temp_range"][1]*1.1
        alloy_display.value = str(oven.sprofile["alloy"])
        profile_display.value = str(oven.sprofile["title"])
        draw_profile(sgraph, oven.sprofile)
def draw_profile(graph, profile):
    """Update the display with current info."""
    # draw stage lines
    # preheat
    graph.draw_line(profile["stages"]["preheat"][0], profile["temp_range"][0],
                    profile["stages"]["preheat"][0], profile["temp_range"][1]
                    * 1.1,
                    GRID_SIZE, GRID_COLOR, GRID_STYLE)
    graph.draw_line(profile["time_range"][0], profile["stages"]["preheat"][1],
                    profile["time_range"][1], profile["stages"]["preheat"][1],
                    GRID_SIZE, GRID_COLOR, GRID_STYLE)
    # soak
    graph.draw_line(profile["stages"]["soak"][0], profile["temp_range"][0],
                    profile["stages"]["soak"][0], profile["temp_range"][1]*1.1,
                    GRID_SIZE, GRID_COLOR, GRID_STYLE)
    graph.draw_line(profile["time_range"][0], profile["stages"]["soak"][1],
                    profile["time_range"][1], profile["stages"]["soak"][1],
                    GRID_SIZE, GRID_COLOR, GRID_STYLE)
    # reflow
    graph.draw_line(profile["stages"]["reflow"][0], profile["temp_range"][0],
                    profile["stages"]["reflow"][0], profile["temp_range"][1]
                    * 1.1,
                    GRID_SIZE, GRID_COLOR, GRID_STYLE)
    graph.draw_line(profile["time_range"][0], profile["stages"]["reflow"][1],
                    profile["time_range"][1], profile["stages"]["reflow"][1],
                    GRID_SIZE, GRID_COLOR, GRID_STYLE)
    # cool
    graph.draw_line(profile["stages"]["cool"][0], profile["temp_range"][0],
                    profile["stages"]["cool"][0], profile["temp_range"][1]*1.1,
                    GRID_SIZE, GRID_COLOR, GRID_STYLE)
    graph.draw_line(profile["time_range"][0], profile["stages"]["cool"][1],
                    profile["time_range"][1], profile["stages"]["cool"][1],
                    GRID_SIZE, GRID_COLOR, GRID_STYLE)
 
    # draw labels
    x = profile["time_range"][0]
    y = profile["stages"]["reflow"][1]
    xp = int(GXSTART + graph.width * (x - graph.xmin)
             // (graph.xmax - graph.xmin))
    yp = int(GHEIGHT * (y - graph.ymin)
             // (graph.ymax - graph.ymin))
 
    label_reflow= plot.text(xp - 10,GHEIGHT - yp - 10,str(profile["stages"]["reflow"][1]), color = palette[2])
 
    # draw time line (horizontal)
    graph.draw_line(graph.xmin-AXIS_SIZE, graph.ymin, graph.xmax,
                    graph.ymin , AXIS_SIZE, AXIS_COLOR, 1)
    graph.draw_line(graph.xmin, graph.ymax, graph.xmax, graph.ymax,
                    AXIS_SIZE, AXIS_COLOR, 1)
    # draw time ticks
    tick = graph.xmin
    while tick < (graph.xmax - graph.xmin):
        graph.draw_line(tick, graph.ymin, tick, graph.ymin + 10,
                        AXIS_SIZE, AXIS_COLOR, 1)
        graph.draw_line(tick, graph.ymax, tick, graph.ymax - 10 - AXIS_SIZE,
                        AXIS_SIZE, AXIS_COLOR, 1)
        tick += 60
 
    # draw temperature line (vertical)
    graph.draw_line(graph.xmin+AXIS_SIZE, graph.ymin, graph.xmin+AXIS_SIZE,
                    graph.ymax, AXIS_SIZE, AXIS_COLOR, 1)
    graph.draw_line(graph.xmax - AXIS_SIZE + 1, graph.ymin,
                    graph.xmax - AXIS_SIZE + 1,
                    graph.ymax, AXIS_SIZE, AXIS_COLOR, 1)
    # draw temperature ticks
    tick = graph.ymin
    while tick < (graph.ymax - graph.ymin)*1.1:
        graph.draw_line(graph.xmin, tick, graph.xmin + 10, tick,
                        AXIS_SIZE, AXIS_COLOR, 1)
        graph.draw_line(graph.xmax, tick, graph.xmax - 10 - AXIS_SIZE,
                        tick, AXIS_SIZE, AXIS_COLOR, 1)
        tick += 50
 
    # draw profile
    x1 = profile["profile"][0][0]
    y1 = profile["profile"][0][1]
    for point in profile["profile"]:
        x2 = point[0]
        y2 = point[1]
        graph.draw_line(x1, y1, x2, y2, PROFILE_SIZE, PROFILE_COLOR, 1)
        x1 = x2
        y1 = y2

def goodbye():
    abort()
    app.destroy()
loadPlot()
app.set_full_screen()
app.when_closed = goodbye
app.display()
