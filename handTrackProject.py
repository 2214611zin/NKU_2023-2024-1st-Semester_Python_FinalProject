import os
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector


class SlideAnnotator:
    def __init__(self, target_path):
        # 初始化手势检测器
        self.detector = HandDetector(detectionCon=0.8, maxHands=1)

        # 图片路径、变量设置
        self.target_path = target_path
        self.images_list = sorted(os.listdir(self.target_path), key=len)
        self.camera_delay = 30
        self.button_pressed = False
        self.counter = 0
        self.draw_mode = False
        self.img_number = 0
        self.delay_counter = 0
        self.annotations = [[]]
        self.annotation_number = -1
        self.annotation_start = False
        self.hs, self.ws = int(120 * 1), int(213 * 1)  # 幻灯片小图像宽高

        # 设置摄像头
        self.total_width, self.total_height = 1280, 720
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.total_width)
        self.cap.set(4, self.total_height)

    def detector_Run(self):
        while True:
            # 获取图像帧
            success, img = self.cap.read()
            img = cv2.flip(img, 1)
            path_full_image = os.path.join(self.target_path, self.images_list[self.img_number])
            currentImage = cv2.imread(path_full_image)

            # 检测手部和手势
            hands, img = self.detector.findHands(img)
            # 画手势阈值线
            cv2.line(img, (0, 300), (self.total_width, 300), (0, 255, 0), 10)

            if hands and not self.button_pressed:  # 如果检测到手部并且没有按下按钮
                hand = hands[0]  # 获取第一只手
                cx, cy = hand["center"]  # 获取手的中心坐标
                lm_list = hand["lmList"]  # 21个关键点的列表
                fingers_detected = self.detector.fingersUp(hand)  # 每个手指的状态

                # 简化绘画操作所需的值
                x_val = int(np.interp(lm_list[8][0], [self.total_width // 2, self.total_width], [0, self.total_width]))
                y_val = int(np.interp(lm_list[8][1], [150, self.total_height - 150], [0, self.total_height]))
                index_finger = x_val, y_val  # 获取食指指尖坐标

                if cy <= 500:  # 如果手在脸的高度
                    if fingers_detected == [1, 0, 0, 0, 0]:  # 如果是左移动手势
                        print("Left")
                        self.button_pressed = True
                        if self.img_number > 0:  # 若当前图片不是第一张，切换到上一张图片
                            self.img_number -= 1
                            self.annotations = [[]]
                            self.annotation_number = -1
                            self.annotation_start = False
                    if fingers_detected == [0, 0, 0, 0, 1]:  # 如果是右移动手势
                        print("Right")
                        self.button_pressed = True
                        if self.img_number < len(self.images_list) - 1:  # 若当前图片不是最后一张，切换到下一张图片
                            self.img_number += 1
                            self.annotations = [[]]
                            self.annotation_number = -1
                            self.annotation_start = False

                if fingers_detected == [0, 1, 1, 0, 0]:  # 如果是手指弯曲，绘制圆点
                    cv2.circle(currentImage, index_finger, 12, (138, 43, 226), cv2.FILLED)

                if fingers_detected == [0, 1, 0, 0, 0]:  # 如果是手指竖立状态，开始注释
                    if not self.annotation_start:
                        self.annotation_start = True
                        self.annotation_number += 1
                        self.annotations.append([])
                    print(self.annotation_number)
                    self.annotations[self.annotation_number].append(index_finger)  # 添加注释点
                    cv2.circle(currentImage, index_finger, 12, (30, 144, 255), cv2.FILLED)

                else:
                    self.annotation_start = False

                if fingers_detected == [0, 1, 1, 1, 0]:  # 如果是三指弯曲状态，撤销上一个注释
                    if self.annotations:
                        self.annotations.pop(-1)
                        self.annotation_number -= 1
                        self.button_pressed = True

            else:
                self.annotation_start = False

            if self.button_pressed:  # 如果按下按钮，延迟一定时间后才可以再次按下
                self.counter += 1
                if self.counter > self.camera_delay:
                    self.counter = 0
                    self.button_pressed = False

            # 绘制注释
            for i, annotation in enumerate(self.annotations):
                for j in range(len(annotation)):
                    if j != 0:
                        cv2.line(currentImage, annotation[j - 1], annotation[j], (30, 144, 255), 12)

            img_small = cv2.resize(img, (self.ws, self.hs))  # 将摄像头的图像帧调整大小
            h, w, _ = currentImage.shape
            currentImage[0:self.hs, w - self.ws: w] = img_small  # 在幻灯片上方显示调整后的摄像头图像

            cv2.imshow("Slides", currentImage)
            cv2.imshow("Image", img)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break


class InteractiveSlideAnnotator:
    def __init__(self, target_path):
        self.annotator = SlideAnnotator(target_path)

    def main_menu(self):
        print("欢迎使用手势演示幻灯片应用！")
        print("-" * 52)
        while True:
            print("请选择要执行的操作：")
            print("1. 启动演示")
            print("2. 获取帮助信息")
            print("3. 退出程序")

            user_choice = input("输入相应的数字以选择操作：")
            print("-" * 52)

            if user_choice == '1':
                self.annotator.detector_Run()
            elif user_choice == '2':
                self.show_help()
            elif user_choice == '3':
                print("感谢使用手势演示应用。再见！")
                break
            else:
                print("无效的输入，请重新输入。")
                print("-" * 52)

    def show_help(self):
        print('>' * 22 + "帮助信息" + "<" * 22)
        print("这是一个手势演示应用，你可以通过手势实现对幻灯片图片的5种不同操作：")
        print("操作1：往后翻页      手势：握拳面向屏幕伸出小拇指")
        print("操作2：往回翻页      手势：握拳面向屏幕伸出大拇指")
        print("操作3：涂鸦标记      手势：握拳面向屏幕伸出食指即可操作")
        print("操作4：删除涂鸦      手势：握拳面向屏幕伸出食指、中指和无名指即可操作")
        print("操作5：光标跟踪      手势：握拳面向屏幕伸出食指和中指即可操作")
        print("-" * 52)


# 创建交互实例对象
interactive_annotator = InteractiveSlideAnnotator("Presentation")
interactive_annotator.main_menu()
