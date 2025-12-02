"""アフィン変換用の座標点選択ツール

OpenCVを使用して画像上の座標点をマウスで選択するGUIを提供します。
異常検知における画像の歪み補正（射影変換）用の座標点を取得するために使用します。
"""

import cv2
import tkinter.filedialog


class ProjectionPointSelector:
    """画像上の座標点を対話的に選択するクラス

    マウス操作で画像上の任意の点を選択し、射影変換に使用する座標を取得します。
    左クリックで点を追加、右クリックで直前の点を削除できます。

    Attributes:
        image: 対象画像（BGR形式のNumPy配列）
        window_name: OpenCVウィンドウ名
        num_points: 選択する座標点の数（デフォルト: 4点）
        points: 選択済み座標のリスト

    Example:
        >>> selector = ProjectionPointSelector()
        >>> points = selector.select_points()
        >>> print(points)  # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        >>> selector.save_to_csv("affine_points.csv")
    """

    def __init__(self, image=None, window_name="MouseEvent", num_points=4):
        self.image = image
        self.window_name = window_name
        self.num_points = num_points
        self.points = []

    def _on_mouse(self, event, x, y, flags, params):
        """マウスイベントのコールバック関数

        左クリックで座標点を追加、右クリックで最後の点を削除します。
        十字線とポリゴンをリアルタイムで描画します。

        Args:
            event: OpenCVマウスイベント
            x: マウスのX座標
            y: マウスのY座標
            flags: イベントフラグ（未使用）
            params: 追加パラメータ（未使用）
        """
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

        cv2.putText(
            img,
            f"({x}, {y})",
            (0, 20),
            cv2.FONT_HERSHEY_PLAIN,
            1,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        cv2.imshow(self.window_name, img)

    def select_points(self):
        """対話的に座標点を選択する

        画像が未設定の場合はファイルダイアログで選択を求めます。
        OpenCVウィンドウ上でマウス操作により座標を選択します。

        操作方法:
            - 左クリック: 座標点を追加
            - 右クリック: 最後の座標点を削除
            - Enter: 選択完了（num_points個選択済みの場合）
            - Esc: キャンセル

        Returns:
            選択された座標のリスト [[x1,y1], [x2,y2], ...]。
            キャンセル時や点数不足の場合は空リスト。

        Note:
            射影変換では通常、左上→右上→右下→左下の順で選択します。
        """
        if self.image is None:
            path = tkinter.filedialog.askopenfilename(
                title="画像を選択してください",
                initialdir=".",
                filetypes=[
                    ("画像ファイル", "*.png *.jpg *.jpeg *.bmp"),
                    ("すべてのファイル", "*.*"),
                ],
            )

            # キャンセルされた場合は空文字列が返される
            if not path:
                print("画像選択がキャンセルされました")
                return []

            self.image = cv2.imread(path)
            if self.image is None:
                print(f"画像が読み込めません: {path}")
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
        """選択した座標をCSVファイルに保存

        各行に "x,y" 形式で座標を出力します。

        Args:
            path: 保存先CSVファイルのパス（デフォルト: "points.csv"）

        Note:
            選択済み座標数がnum_pointsと一致しない場合は保存されません。

        Example:
            >>> selector.save_to_csv("affine_points.csv")
            座標を affine_points.csv に保存しました
        """
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
