import org.bytedeco.javacpp.Loader;
import org.bytedeco.opencv.global.opencv_core;
import org.bytedeco.opencv.global.opencv_highgui;
import org.bytedeco.opencv.global.opencv_imgcodecs;
import org.bytedeco.opencv.global.opencv_imgproc;
import org.bytedeco.opencv.opencv_core.*;

public class Img {

    static { Loader.load(opencv_core.class); }

    private Mat img = new Mat();

    /* ---------- loading & resize ---------- */
    public Img read(String path,
                    Size size,
                    boolean keepAspect,
                    int interpolation) {

        img = opencv_imgcodecs.imread(path,
                                      opencv_imgcodecs.IMREAD_UNCHANGED);
        if (img.empty())
            throw new IllegalArgumentException("Cannot load image: " + path);

        if (size != null) {
            int w = img.cols(), h = img.rows();
            int targetW = (int) size.width();
            int targetH = (int) size.height();

            int newW, newH;
            if (keepAspect) {                              // keep long side inside target box
                double s = Math.min(targetW / (double) w,
                                     targetH / (double) h);    // :contentReference[oaicite:4]{index=4}
                newW = (int) Math.round(w * s);
                newH = (int) Math.round(h * s);
            } else {
                newW = targetW;  newH = targetH;
            }
            opencv_imgproc.resize(img, img,
                                  new Size(newW, newH),
                                  0, 0, interpolation);
        }
        return this;
    }

    public Img read(String path) {
        return read(path, null, false, opencv_imgproc.INTER_AREA);
    }

    /* ---------- compositing ---------- */
    public void drawOn(Img other, int x, int y) {

        if (img.empty() || other.img.empty())
            throw new IllegalStateException("Both images must be loaded.");

        /* 1. ensure same channel count ------------------------------------- */
        if (img.channels() != other.img.channels()) {
            if (img.channels() == 3 && other.img.channels() == 4)
                opencv_imgproc.cvtColor(img, img,
                                        opencv_imgproc.COLOR_BGR2BGRA);   // :contentReference[oaicite:5]{index=5}
            else if (img.channels() == 4 && other.img.channels() == 3)
                opencv_imgproc.cvtColor(img, img,
                                        opencv_imgproc.COLOR_BGRA2BGR);
        }

        int w = img.cols(), h = img.rows();
        int W = other.img.cols(), H = other.img.rows();
        if (x + w > W || y + h > H)
            throw new IllegalArgumentException("Patch exceeds target bounds.");

        /* 2. get ROI ------------------------------------------------------- */
        Mat roi = other.img.apply(new Rect(x, y, w, h));

        /* 3. alpha‑aware copy --------------------------------------------- */
        if (img.channels() == 4) {
            // split BGRA, grab A as mask
            MatVector bgra = new MatVector();
            opencv_core.split(img, bgra);                       // MatVector! :contentReference[oaicite:6]{index=6}
            Mat alpha = bgra.get(3);

            // convert BGRA→BGR then copy with mask (fast path)   :contentReference[oaicite:7]{index=7}
            Mat bgr = new Mat();
            opencv_imgproc.cvtColor(img, bgr,
                                    opencv_imgproc.COLOR_BGRA2BGR);
            bgr.copyTo(roi, alpha);                             // copyTo(dst, mask)
        } else {
            img.copyTo(roi);
        }
    }

    /* ---------- text ---------- */
    public void putText(String txt,
                        int x, int y,
                        double fontSize,
                        Scalar color,
                        int thickness) {

        opencv_imgproc.putText(
                img, txt, new Point(x, y),
                opencv_imgproc.FONT_HERSHEY_SIMPLEX,
                fontSize, color, thickness,
                opencv_imgproc.LINE_AA,
                false);                                   // bottomLeftOrigin  :contentReference[oaicite:8]{index=8}
    }

    /* ---------- display ---------- */
    public void show() {
        if (img.empty()) throw new IllegalStateException("Image not loaded.");
        opencv_highgui.imshow("Image", img);
        opencv_highgui.waitKey(0);
        opencv_highgui.destroyAllWindows();
    }

    /* ---------- util ---------- */
    public Mat mat() { return img; }
}
