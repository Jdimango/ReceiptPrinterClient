
from escpos.printer import Usb
from escpos import *
import time
import requests
from PIL import Image, ImageOps, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True



p = Usb(0x0416, 0x5011, 0, 0x81, 0x03)
p.charcode('USA')


endpoint = "https://shielded-crag-36267.herokuapp.com/get_jobs"


queue=[]

def connect_to_printer():
    global p
    try:
        p = printer.Usb(0x0416, 0x5011, 4, 0x81, 0x03,timeout=5,)
    except Exception as e:
        print(e)
        return False
    





def print_text(name,text):
    try:
        p.text(" \n")
        p.text(name)
        p.text(" \n")
        p.text(text.encode("ascii", errors="ignore").decode()+'\n')
        return True
    except Exception as e:
        print(e)
        return False
    
    
    
    
    
def print_qr(name,qr_data):
    try:
        p.text(" \n")
        p.text(name)
        p.text(" \n")
        p.qr(qr_data)
        return True
    except Exception as e:
        print(e)
        return False




def print_image(name,url):
    try:
        response = requests.get(url)

        if(response.status_code != 200):
            print('Image does not exist')
            p.text(" \n")
            p.text(name)
            p.text(" \n")
            p.text('Tried to print a video?')
            return True

        with open("downloaded_img.png", "wb") as file:
            file.write(response.content)


        image = Image.open("downloaded_img.png").convert("RGBA")

        image.thumbnail((400,10000000), Image.ANTIALIAS)

        new_image = Image.new("RGBA", image.size, "WHITE")

        new_image.paste(image,(0,0), mask=image)

        gray_image = ImageOps.grayscale(new_image)

        gray_image.convert("RGB")

        gray_image.save("new.jpg", quality=50)

        p.text(" \n")
        p.text(name)
        p.text(" \n")
        p.image('new.jpg')

        return True
    
    except Exception as e:
        print(e)
        return False
    
    
    
    
    
def get_jobs():
    global queue
    try:
        r = requests.post(endpoint)
        print(r.json())
        if r.status_code == 200 and len(r.json()) > 0:
            for job in r.json():
                job['tries'] = 0
                queue.append(job)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False
    
    
def execute_all_jobs():
    global queue
    while len(queue) > 0:

        job = queue.pop(0)
        p.text(" \n")
        
        if(job['type']) == 'text':
            
            if print_text(job['name'],job['content']):
                print("Success")
            
            else:
                if(job['tries'] < 3):
                    job['tries'] += 1
                    queue.append(job)
                    print("Failed, trying again")
                else:
                    print("Failed, giving up") 

            continue
            
        # if(job['type']) == 'qr':
            
        #     if print_qr(job['name'],job['content']):
        #         print("Success")
            
        #     else:
        #         if(job['tries'] < 3):
        #             job['tries'] += 1
        #             queue.append(job)
        #             print("Failed, trying again")
        #         else:
        #             print("Failed, giving up") 
        #     continue
            
        if(job['type']) == 'image':
            
            if print_image(job['name'],job['content']):
                print("Success")
                url = job['content'].replace('image','delete',1)
                result = requests.get(f"{url}")
                if(result.text == 'success'):
                    print("Image deleted")
                elif (result.text == 'does not exist'):
                    print("Image does not exist")
                else:
                    print("Failed")
                    job['type'] = 'delete'
                    queue.append(job)
            
            else:
                if(job['tries'] < 3):
                    job['tries'] += 1
                    queue.append(job)
                    print("Failed, trying again")
                else:
                    print("Failed, giving up") 
            continue

        if(job['type']) == 'delete':
            
            url = job['content'].replace('image','delete',1)
            result = requests.get(f"{url}")
            if(result.text == 'success'):
                print("Image deleted")
            elif (result.text == 'does not exist'):
                print("Image does not exist")
            else:
                if(job['tries'] < 3):
                    job['tries'] += 1
                    queue.append(job)
                    print("Failed, trying again")
                else:
                    print("Failed, giving up") 

            continue
            
    return True


while True:

    if not get_jobs():
        print("Failed to get jobs")
        time.sleep(10)
        continue
        
    if execute_all_jobs():
        print("Successfully executed all jobs")
        p.cut()
        # queue=[{'type':'text', 'content':'Hello World'},{'type':'image', 'content':'https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png'}]
        # continue 
        
    time.sleep(2)