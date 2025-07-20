import org.bytedeco.opencv.global.opencv_imgproc;
import org.bytedeco.opencv.opencv_core.Scalar;
import org.bytedeco.opencv.opencv_core.Size;

public class Example {

    public static void main(String[] args) {

        // Adjust these paths to any test pictures you have
        String background = "C:\\Users\\Yehudit\\Downloads\\code\\SimpleImg\\board.png";
        String logo       = "C:\\Users\\Yehudit\\Downloads\\code\\SimpleImg\\pieces\\QW\\states\\jump\\sprites\\2.png";

        Img canvas = new Img().read(background);                       // original size
        Img piece  = new Img().read(logo,
                                    new Size(100, 1010),  // resize to 100×100
                                    true,                // keep aspect
                                    opencv_imgproc.INTER_AREA);

        piece.putText("Demo", 10, 30, 1.0,
                      new Scalar(255, 0, 0, 255), 2);                  // blue text

        piece.drawOn(canvas, 50, 50);                                  // blend top‑left
        canvas.show();
    }
}
