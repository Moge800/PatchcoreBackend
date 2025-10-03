import cv2
import tkinter.filedialog


class ProjectionPointSelector:
    def __init__(self, image=None, window_name="MouseEvent", num_points=4):
        self.image = image
        self.window_name = window_name
        self.num_points = num_points
        self.points = []

    def _on_mouse(self, event, x, y, flags, params):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(self.points) < self.num_points:
                self.points.append([x, y])
        elif event == cv2.EVENT_RBUTTONDOWN:
            if self.points:
                self.points.pop(-1)

        img = self.image.copy()
        h, w = img.shape[:2]
        cv2.line(img, (x, 0), (x, h), (255, 0, 0), 1)
        cv2.line(img, (0, y), (w, y), (255, 0, 0), 1)

        for i, pt in enumerate(self.points):
            cv2.circle(img, tuple(pt), 3, (0, 0, 255), 3)
            if i > 0:
                cv2.line(img, tuple(self.points[i - 1]), tuple(pt), (0, 255, 0), 2)
            if i == self.num_points - 1:
                cv2.line(img, tuple(pt), tuple(self.points[0]), (0, 255, 0), 2)

        if 0 < len(self.points) < self.num_points:
            cv2.line(img, (x, y), tuple(self.points[-1]), (0, 255, 0), 2)

        cv2.putText(img, f"({x}, {y})", (0, 20), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.imshow(self.window_name, img)

    def select_points(self):
        if self.image is None:
            path = tkinter.filedialog.askopenfilename(
                title="画像を選択してください",
                initialdir=".",
                filetypes=[("画像ファイル", "*.png *.jpg *.jpeg *.bmp"), ("すべてのファイル", "*.*")],
            )
            self.image = cv2.imread(path)
            if self.image is None:
                print("画像が読み込めません")
                return []

        print("左クリックでポイント追加, 右クリックでポイント削除")
        print("順番は左上, 右上, 右下, 左下です")
        print("ポイント数が4つになったらEnterを押してください")
        print("終了する場合はEscを押してください")
        print("画像ウィンドへ切り替えて作業してください")

        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self._on_mouse, None)
        cv2.imshow(self.window_name, self.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        if len(self.points) != self.num_points:
            print("ポイント数が不足しています")
            return []

        return self.points

    def save_to_csv(self, path="points.csv"):
        if len(self.points) != self.num_points:
            print("保存できるポイント数ではありません")
            return
        with open(path, "w") as f:
            for x, y in self.points:
                f.write(f"{x},{y}\n")
        print(f"座標を {path} に保存しました")


if __name__ == "__main__":
    selector = ProjectionPointSelector()
    points = selector.select_points()
    print(points)
