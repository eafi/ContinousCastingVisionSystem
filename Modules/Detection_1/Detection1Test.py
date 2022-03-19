from os import path
from Modules.Detection_1.search import search
from utils.PnP import *
from glob import glob


if __name__ == '__main__':
    file = f'./CL/*.png'
    files = glob(file)
    log = open('log.txt', 'w')
    log.write('========\n')
    log.close()
    for file in files:
        log = open('log.txt', 'a')
        log.write('========\n' + file)
        log.close()
        if path.isfile(file):
            print('processing...', path)
            src = cv2.imread(file, flags=cv2.IMREAD_GRAYSCALE)
            srcF = src.astype(np.float32)
            bgr_src = cv2.cvtColor(src, cv2.COLOR_GRAY2BGR)
            cv2.imshow('result', bgr_src)
            rect = search(src_img=srcF)
            if rect is not None:
                cv2.line(bgr_src, rect[0].astype(np.int32), rect[1].astype(np.int32), (0, 255, 255), 1)
                cv2.line(bgr_src, rect[1].astype(np.int32), rect[2].astype(np.int32), (0, 255, 255), 1)
                cv2.line(bgr_src, rect[2].astype(np.int32), rect[3].astype(np.int32), (0, 255, 255), 1)
                cv2.line(bgr_src, rect[3].astype(np.int32), rect[0].astype(np.int32), (0, 255, 255), 1)
                imgpts, rvec, tvec = pnp(rect, cameraMatrx, cameraDist)

                print('top len: ', abs(np.linalg.norm(rect[0] - rect[1], ord=2)))
                print('left len: ',abs(np.linalg.norm(rect[1] - rect[2], ord=2)))
                print('bot len: ', abs(np.linalg.norm(rect[2] - rect[3], ord=2)))
                print('right len:',abs(np.linalg.norm(rect[3] - rect[0], ord=2)))
                bgr_src = draw(bgr_src, rect, imgpts)
                cv2.imshow('result', bgr_src)
            cv2.waitKey(0)
            cv2.destroyWindow(file)
    #points = np.random.rand(4,2).tolist()
    #search_rect(points)

