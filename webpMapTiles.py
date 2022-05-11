import multiprocessing as mp
import webp
import os 
import numpy as np
import cv2
import argparse
from PIL import Image
from skimage import io

parser = argparse.ArgumentParser(prog='webpMapTiles.py', description='Generate tiles from png, jpg or tif images') 

parser.add_argument('--input', '-i', type=str, required=True,  help='Folder of input images')
parser.add_argument('--output', '-o', type=str, required=True,  help='Folder of output tiles')
parser.add_argument('--lossless', '-l', type=bool, default=False, required=False,  help='Generate lossless compressed webp tiles?')
parser.add_argument('--quality', '-q', type=int, default=-1, required=False,  help='Quality of webp tiles, an integer between 0-100')


args = parser.parse_args()

def tileGenerator(img,length,width,divScale,zoomScale,scale,enlarge,root,lossless,quality):
    #創建一個都是0(全黑)的影像
    pad = np.zeros(shape = (int(512*(divScale**scale)),int(512*(divScale**scale)),3))
    #把原圖縮放為當前圖磚階層的大小
    resize = cv2.resize(img, dsize=(int(width/(divScale**(zoomScale - scale))),int(length/(divScale**(zoomScale - scale)))), interpolation=cv2.INTER_AREA)
    #把縮放後的圖疊在全黑影像的左上方
    pad[0:int(length/(divScale**(zoomScale - scale))),0:int(width/(divScale**(zoomScale - scale))),:] = resize
    pad = (pad).astype('uint8')

    #這裡創建"階層"的目錄
    #先確定目錄的路徑
    parent = str(scale) + '/'
    parentPath = os.path.join(root,parent)
    #創建資料夾
    os.mkdir(parentPath)

    for i in range(int(length/(divScale**(zoomScale - scale)))//512+1):
        #這裡創建"行"的目錄
        son = str(i) + '/'
        sonPath = os.path.join(parentPath,son)
        os.mkdir(sonPath)

        for j in range(int(width/(divScale**(zoomScale - scale)))//512+1):
            #把圖磚從大圖裡面clip出來
            tile = pad[512*i:512*(i+1),512*j:512*(j+1),:]
            #轉換成webp套件需要的格式
            pil_tile=Image.fromarray(tile)
            #儲存webp檔
            if quality < 0 and quality != -1:
                raise ValueError("quality must be an integer between 0 - 100")
            elif quality > 100 :
                raise ValueError("quality must be an integer between 0 - 100")
            elif quality < 0 and quality == -1:

                if not lossless:
                    webp.save_image(pil_tile, sonPath + "%d.webp"%(j))
                else:
                    webp.save_image(pil_tile, sonPath + "%d.webp"%(j), lossless = True)

            else:
                if not lossless:
                    webp.save_image(pil_tile, sonPath + "%d.webp"%(j), quality = int(quality))
                else:
                    webp.save_image(pil_tile, sonPath + "%d.webp"%(j), quality = int(quality), lossless = True)
    del resize
    del pad
    print(f"{scale+1}/{zoomScale+enlarge+1}",root)

def webpTileGenerator(folder, output_path, Zoom = 0, Scale = 2, lossless = False, quality = -1):
    
    Folder = os.listdir(folder)
    for file in Folder:
        #讀圖
        image_path = folder + '/' + file
        img = io.imread(image_path)[:,:,0:3]
        length,width = img.shape[0],img.shape[1]
        #image names with image shape
        Output_path = os.path.join(output_path, f'{file[:-4]}_{length}_{width}')
        if not os.path.isdir(Output_path):
            os.mkdir(Output_path)
        #儲存圖磚的根目錄
        root = Output_path + '/'

        divScale = Scale
        #這裡看原圖能被除以2(或是另外設定的Scale)幾次(小於512就終止)
        for division in range(23):
            zoomScale = division
            if max(img.shape)/(divScale**(division)) <= 512:
                break
        
        # not useful
        if Zoom == 0:
            enlarge = 0
        elif Zoom < 0 or Zoom >23:
            raise ValueError("Zoom需為大於0並小於24的整數")
        else:
            enlarge = int(Zoom) - zoomScale

        if __name__=='__main__':

            process_list = []
            # multi-process
            for scale in range(zoomScale+1+enlarge):
                process_list.append(mp.Process(target = tileGenerator, args = (img,length,width,divScale,zoomScale,scale,enlarge,root,lossless,quality)))
                process_list[scale].start()

webpTileGenerator(args.input, args.output, lossless = args.lossless, quality = args.quality)