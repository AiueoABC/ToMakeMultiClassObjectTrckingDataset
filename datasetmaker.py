import cv2
import numpy as np
import PySimpleGUI as sg
import glob
import os


def imread(filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8):
    try:
        n = np.fromfile(filename, dtype)
        img = cv2.imdecode(n, flags)
        return img
    except Exception as e:
        print(e)
        return None

id2cls = {
    0: 'pedestrian',
    1: 'people',
    2: 'bicycle',
    3: 'car',
    4: 'van',
    5: 'truck',
    6: 'tricycle',
    7: 'awning-tricycle',
    8: 'bus',
    9: 'motor',
    10: 'others'
}

sg.theme('LightBlue')

layout = [
        [sg.Text('Labeling', size=(40, 1), justification='center', font='Helvetica 18', key='-status-')],
        [sg.Text('Image Path Root: ', size=(15, 1), font='Helvetica 14'),
         sg.InputText(default_text='/imgpath', size=(70, 1), key='-root_path-'),
         sg.FolderBrowse('Browse', size=(10, 1), font='Helvetica 14', key='-browse-'),
         sg.Button('Open', size=(10, 1), font='Helvetica 14', key='-open-')
         ],
        [sg.Text('CID: ', size=(10, 1), font='Helvetica 14', key='-cid-'),
         sg.InputText(default_text='0', size=(10, 1), key='-cid_input-'),
         sg.Button('SET', size=(10, 1), font='Helvetica 14', key='-set_cid-'),
         sg.Text('-', size=(20, 1), font='Helvetica 14', key='-cid_label-')],
        [sg.Text('TID: ', size=(10, 1), font='Helvetica 14', key='-tid-'),
         sg.InputText(default_text='0', size=(10, 1), key='-tid_input-'),
         sg.Button('SET', size=(10, 1), font='Helvetica 14', key='-set_tid-'),
         sg.Text(' ', size=(5, 1), font='Helvetica 14'),
         sg.Checkbox('Use Original Frame For MagWindow', key='-use_original-')],
        # [sg.Image(filename='', key='image')],
        [sg.Button('Box', size=(10, 1), font='Helvetica 14', key='-box-'),
         sg.Button('Add', size=(10, 1), font='Helvetica 14', key='-add-'),
         sg.Button('Erase', size=(10, 1), font='Helvetica 14', key='-erase-'),
         sg.Button('Cancel', size=(10, 1), font='Helvetica 14', key='-cancel-'),
         sg.Button('<<=== forward', size=(13, 1), font='Helvetica 14', key='-back-'),
         sg.Button('  next  ===>>', size=(13, 1), font='Helvetica 14', key='-next-'),
         sg.Button('SAVE', size=(10, 2), font='Helvetica 14', key='-save-')
         ],
        [sg.Button('Exit', size=(10, 1), font='Helvetica 14', key='-exit-'),
         sg.Text('Image: \nText: ', size=(100, 2), font='Helvetica 8', key='-fname-')
         ]
        ]


window = sg.Window('Labeling', layout, location=(300, 300))


coordinates = [-1, -1]
mode = 0
rb_switch = False
rb_switch_changed = False
rb_coordinates = [-1, -1]

def update_coordinates(event, x, y, flags, param):
    # For mouse event
    global coordinates, rb_switch, rb_switch_changed, rb_coordinates
    if event == cv2.EVENT_LBUTTONDOWN:
        coordinates = [x, y]
    if event == cv2.EVENT_RBUTTONDOWN:
        rb_switch_changed = True
        rb_switch = False if rb_switch else True
    rb_coordinates = [x, y]
# box lists to control
box_list = []
def box_add_erase(frame):
    global mode, box_list
    color = (0, 255, 0) if mode == 1 else (0, 0, 255)
    if len(box_list) == 0:
        box_list = [[mode, coordinates]]
        frame = cv2.circle(frame, tuple(coordinates), 2, color, -1)
    else:
        if len(box_list[-1]) < 5:
            if box_list[-1][0] == mode:
                box_list[-1].append(coordinates)
                frame = cv2.circle(frame, tuple(coordinates), 2, color, -1)
                if len(box_list[-1]) == 5:
                    x_list = [c[0] for c in box_list[-1][1:]]
                    y_list = [c[1] for c in box_list[-1][1:]]
                    x0, y0, x1, y1 = min(x_list), min(y_list), max(x_list), max(y_list)
                    cv2.rectangle(frame, (x0, y0), (x1, y1), color, thickness=1)
            else:
                box_list = box_list[:-1]
        else:
            # first time of this box
            box_list.append([mode, coordinates])
            frame = cv2.circle(frame, tuple(coordinates), 2, color, -1)
    return frame


# GUI section and cv2 section
fnames = []
save_list = []
cv2.namedWindow('q=EXIT,f=Forward,b=Back', cv2.WINDOW_NORMAL)
cv2.setMouseCallback('q=EXIT,f=Forward,b=Back', update_coordinates)
count = 0
img_opened = False
img_changed = False
cid = 0
tid = 0
while True:
    if img_changed:
        fname = fnames[count]
        frame = imread(fname)
        orig_frame = frame.copy()
        height, width, channels = frame.shape[:3]

        img_changed = False
        # read from file
        savefile = f'{os.path.splitext(fname)[0]}.txt'
        if os.path.exists(savefile):
            # read it
            with open(savefile) as f:
                data = f.read().splitlines()
            for d_str in data:
                cid, tid, cx, cy, bw, bh = d_str.split(' ')
                x0 = int((float(cx) - float(bw) / 2) * width)
                x1 = int((float(cx) + float(bw) / 2) * width)
                y0 = int((float(cy) - float(bh) / 2) * height)
                y1 = int((float(cy) + float(bh) / 2) * height)
                cv2.rectangle(frame, (x0, y0), (x1, y1), (255, 0, 255), thickness=1)
                cv2.putText(frame, f't{tid},c{cid}', (x0, y1), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 3)
                cv2.putText(frame, f't{tid},c{cid}', (x0, y1), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
            save_list = data
            window['-fname-'].update(f'Image: {os.path.basename(fname)}\n Text: {os.path.basename(savefile)}')
            print(f'Load {savefile}:\n' + '\n'.join(save_list))
        else:
            save_list = []
            window['-fname-'].update(f'Image: {os.path.basename(fname)}\n Text: Not Exist')
        if mode == 4:
            censoring_positions[count] = []
        if len(censoring_positions[count]) > 0:
            for cid, tid, x0, y0, x1, y1 in censoring_positions[count]:
                cv2.rectangle(frame, (x0, y0), (x1, y1), (255, 0, 0), thickness=1)
                cv2.putText(frame, f't{tid},c{cid}', (x0, y1), cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 0), 3)
                cv2.putText(frame, f't{tid},c{cid}', (x0, y1), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 2)
                # calculate for save these
                box_height, box_width = y1 - y0, x1 - x0
                center_x, center_y = x1 - box_width / 2, y1 - box_height / 2
                line = f'{cid} {tid} {center_x/width} {center_y/height} {box_width/width} {box_height/height}'
                ids2check = f'{cid} {tid}'
                if ids2check in save_list:  # id already exists, ignore
                    pass
                else:
                    save_list.append(line)
        # erase unnecessary lines
        if mode == 3:
            mode = 0
            try:
                # for box in box_list:
                #     x_list = [c[0] for c in box[1:]]
                #     y_list = [c[1] for c in box[1:]]
                #     safe_list = []
                #     x_min, y_min, x_max, y_max = min(x_list), min(y_list), max(x_list), max(y_list)
                #     for d_str in save_list:
                #         cid, tid, cx, cy, bw, bh = d_str.split(' ')
                #         x0 = int((float(cx) - float(bw) / 2) * width)
                #         x1 = int((float(cx) + float(bw) / 2) * width)
                #         y0 = int((float(cy) - float(bh) / 2) * height)
                #         y1 = int((float(cy) + float(bh) / 2) * height)
                #         if x_min <= x0 <= x_max and x_min <= x1 <= x_max and y_min <= y0 <= y_max and y_min <= y0 <= y_max:
                #             pass
                #         else:
                #             safe_list.append([cid, tid, x0, y0, x1, y1])
                #     censoring_positions[count] = safe_list
                box_list = []
                window['-status-'].update(f'Erased')
            except Exception as e:
                print(e)
        window['-cid-'].update(f'CID:{cid}')
        window['-cid_label-'].update(id2cls[int(cid)])
        window['-tid-'].update(f'TID:{int(tid)}')

        # save txt
        if mode == 2:
            with open(savefile, 'w') as f:
                f.write('\n'.join(save_list))
            print(f'Save to {savefile}:\n' + '\n'.join(save_list))
            mode = 0
            window['-status-'].update(f'Saved')
            window['-fname-'].update(f'Image: {os.path.basename(fname)}\n Text: {os.path.basename(savefile)} (-SAVED-)')

    event, values = window.read(timeout=20)
    x,y = coordinates

    img_changed = False
    if event in (None, '-exit-'):
        break
    elif event == '-open-':
        fileroot = rf"{values['-root_path-']}"
        if os.path.exists(fileroot):
            fnames = glob.glob(f'{fileroot}/*.jpg')
            fnames.extend(glob.glob(f'{fileroot}/*.png'))
            fnames = [fname.replace('\\', '/') for fname in fnames]
            censoring_positions = [[] for i in range(len(fnames))]
            img_changed = True
            img_opened = True
            frame = imread(fnames[count])

    elif event == '-save-':
        mode = 2
        img_changed = True
    elif event == '-box-':
        if mode == 0:
            window['-status-'].update(f'BoxMode: {count} of {len(fnames)}')
        else:
            window['-status-'].update(f'Browse')
        mode = 1 if mode == 0 else 0
    elif event == '-add-':
        img_changed = True
        if len(box_list) > 0:
            if len(box_list[-1]) < 5:
                box_list = box_list[:-1]
            try:
                for box in box_list:
                    x_list = [c[0] for c in box[1:]]
                    y_list = [c[1] for c in box[1:]]
                    x0, y0, x1, y1 = min(x_list), min(y_list), max(x_list), max(y_list)
                    censoring_positions[count].append([cid, tid, x0, y0, x1, y1])
                    box_list = []
            except Exception as e:
                print(e)
    elif event == '-erase-':
        mode = 3
        img_changed = True
        if len(box_list) > 0:
            if len(box_list[-1]) < 5:
                box_list = box_list[:-1]
            try:
                for box in box_list:
                    x_list = [c[0] for c in box[1:]]
                    y_list = [c[1] for c in box[1:]]
                    safe_list = []
                    x_min, y_min, x_max, y_max = min(x_list), min(y_list), max(x_list), max(y_list)
                    for idx, positions in enumerate(censoring_positions[count]):
                        cid, tid, x0, y0, x1, y1 = positions
                        if x_min <= x0 <= x_max and x_min <= x1 <= x_max and y_min <= y0 <= y_max and y_min <= y0 <= y_max:
                            pass
                        else:
                            safe_list.append(positions)
                    # for d_str in save_list:
                    #     cid, tid, cx, cy, bw, bh = d_str.split(' ')
                    #     x0 = int((float(cx) - float(bw) / 2) * width)
                    #     x1 = int((float(cx) + float(bw) / 2) * width)
                    #     y0 = int((float(cy) - float(bh) / 2) * height)
                    #     y1 = int((float(cy) + float(bh) / 2) * height)
                    #     if x_min <= x0 <= x_max and x_min <= x1 <= x_max and y_min <= y0 <= y_max and y_min <= y0 <= y_max:
                    #         pass
                    #     else:
                    #         safe_list.append([cid, tid, x0, y0, x1, y1])
                    censoring_positions[count] = safe_list

            except Exception as e:
                print(e)
    elif event == '-cancel-':
        mode = 4
        img_changed = True
    elif event == '-back-' and img_opened:
        mode = 1
        count -= 1
        if count < 0:
            count = len(fnames) - 1
        img_changed = True
        if mode == 1:
            window['-status-'].update(f'BoxMode: {count} of {len(fnames)}')
        box_list = []
    elif event == '-next-' and img_opened:
        mode = 1
        count += 1
        if count > len(fnames) - 1:
            count = 0
        img_changed = True
        if mode == 1:
            window['-status-'].update(f'BoxMode: {count} of {len(fnames)}')
        box_list = []
    elif event == '-set_cid-':
        cid = values['-cid_input-']
        try:
            window['-cid-'].update(f'CID:{cid}')
            window['-cid_label-'].update(id2cls[int(cid)])
        except:
            cid = 0
            window['-cid-'].update(f'CID:{cid}')
            window['-cid_label-'].update(id2cls[int(cid)])
    elif event == '-set_tid-':
        tid = values['-tid_input-']
        try:
            window['-tid-'].update(f'TID:{int(tid)}')
        except:
            tid = 0
            window['-tid-'].update(f'TID:{int(tid)}')
    if mode == 1 and 0 <= x <= width and 0 <= y <= height:
        # add box mode
        frame = box_add_erase(frame)
        coordinates = [-1, -1]
    else:
        coordinates = [-1, -1]

    if rb_switch:
        rb_switch_changed = False
        center_coordinates = (int(0.5 * width), int(0.5 * height))
        magnifying_w, magnifying_h = 250, 250  # int(0.1 * width), int(0.1 * width)
        window_size = (int(0.3 * width), int(0.3 * height))
        xm, ym = rb_coordinates
        x_tl, y_tl, x_br, y_br = int(xm - magnifying_w / 2), int(ym - magnifying_h / 2), int(xm + magnifying_w / 2), int(ym + magnifying_h / 2)
        x_p, y_p = 125, 125
        # if in edge
        if x_tl < 0:
            x_p += x_tl
            x_tl, x_br = 0, magnifying_w
        elif x_br > width:
            x_p += x_br - width
            x_tl, x_br = width - magnifying_w, width
        if y_tl < 0:
            y_p += y_tl
            y_tl, y_br = 0, magnifying_h
        elif y_br > height:
            y_p += y_br - height
            y_tl, y_br = height - magnifying_h, height
        # cv.imshow('magnifying mode', cv.resize(frame[y_tl:y_br, x_tl:x_br], window_size))
        if values['-use_original-']:
            mag_frame = orig_frame[y_tl:y_br, x_tl:x_br].copy()
        else:
            mag_frame = frame[y_tl:y_br, x_tl:x_br].copy()
        h, w, c = mag_frame.shape[:3]
        cv2.line(mag_frame, (int(w / 2), 0), (int(w / 2), h), (60, 60, 60), thickness=1)
        cv2.line(mag_frame, (0, int(h / 2)), (w, int(h / 2)), (60, 60, 60), thickness=1)
        cv2.circle(mag_frame, (int(w / 2), int(h / 2)), int(0.5 * w), (60, 60, 60), thickness=1)
        cv2.circle(mag_frame, (int(w / 2), int(h / 2)), int(0.2 * w), (60, 60, 60), thickness=1)
        cv2.circle(mag_frame, (x_p, y_p), 1, (0, 0, 255), thickness=-1)
        cv2.imshow('magnifying mode', cv2.resize(mag_frame, (500, 500)))
    elif not rb_switch and rb_switch_changed:
        try:
            cv2.destroyWindow('magnifying mode')
        except:
            pass
    if img_opened:
        cv2.imshow('q=EXIT,f=Forward,b=Back', frame)
        key = cv2.waitKey(5)
        if key == 32:
            window['-use_original-'].update(not values['-use_original-'])

window.close()
cv2.destroyAllWindows()
