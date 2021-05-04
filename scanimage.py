import os
import glob
from csv import DictWriter
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./credentials.json"

global scanned
global successTimes
global failedTimes
global successScore
global topAmount

## TODO
# - Format the tags in: [[name, tag],[name,tag]]
# - Remove ./ from name in final dict

# Set stats to 0
successTimes = 0
failedTimes = 0
scanned = 0

## CONFIG  ##
subFoldersToCheck = ["Default","Clarity","Contrast","Omgedraaid_cats","Spiegel","Temperature"] # <-- This checks in the subfolders, make sure they exist!
successList     = ["Cat","Felidae","Small to medium-sized cats","Domestic short-haired cat"] # <-- This is what counts as a "correct" search from the API
successScore    = 0.90 # <-- Minimal required score to count as correct (0 - 1)
topAmount       = 5 # <-- Only check the top X given labels

def detect_labels(path):
    """Detects labels in the file."""
    from google.cloud import vision
    import io
    print(f"SCANNING IMAGE: {path}")
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.label_detection(image=image)
    labels = response.label_annotations

    returnlabels = []

    ## for temp debugging :)
    print('Labels:')
    for label in labels:
        addToList = {
            "tag": label.description,
            "score": round(label.score,3)
        }
        print(addToList)
        returnlabels.append(addToList)
        
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    else:
        print("SCANNING DONE")
        return returnlabels

def top5cat(labels):
    global successTimes
    global failedTimes
    global successList
    global successScore
    global topAmount
    
    ##print("EVALUATING IMAGE")
    
    success = False
   
    ## Go through each word in the wordlist
    for word in successList:
        ## The given array is already sorted based on score, go through the top X of labels
        
        ## Check if we have enough labels (avoid nullpointering)
        amountOfLabels = len(labels)
        checkAmount = topAmount - 1 # <-- Index starts at 0, so we need to do -1
        if amountOfLabels < checkAmount:
            checkAmount = amountOfLabels - 1 # <-- Index starts at 0, so we need to do -1

        # Now loops as much as u can or given as top through each word
        for x in range(0, checkAmount):
            label = labels[x]
            
            ## Check if a word matches a label
            if word == label['tag']:
                ## Check if the label had a high enough score
                if label['score'] > successScore:
                    success = True

    ## Evaluation, tally and return
    if success:
        successTimes = successTimes + 1
        return True
    else:
        failedTimes = failedTimes + 1
        return False
    
# Get a list of all the images 
allImages = []
detectedImages = []

for foldername in subFoldersToCheck:
    allPNGImages = glob.glob(f"./{foldername}/*.jpg")
    allJPGImages = glob.glob(f"./{foldername}/*.png")
    allJPEGImages = glob.glob(f"./{foldername}/*.jpeg")
    allImages = allImages + allPNGImages + allJPGImages + allJPEGImages


## Everything has been setup, give a clear start signal
print(f"Starting! Images found:", len(allImages))
for image in allImages:
    ## Try to detect the image with the google API
    #labeledImage = detect_labels(image)
    labeledImage = [{'tag': 'Cat', 'score': 0.965}, {'tag': 'Felidae', 'score': 0.919}, {'tag': 'Carnivore', 'score': 0.907}, {'tag': 'Small to medium-sized cats', 'score': 0.885}, {'tag': 'Window', 'score': 0.851}, {'tag': 'Whiskers', 'score': 0.848}, {'tag': 'Iris', 'score': 0.846}, {'tag': 'Snout', 'score': 0.771}, {'tag': 'Fur', 'score': 0.684}, {'tag': 'Domestic short-haired cat', 'score': 0.681}]

    ## Check if the given labels flag a success!
    success = top5cat(labeledImage)

    ## Collecting data from file
    pathname = image
    imagename, imageformat = image.rsplit('.',1)
    imagename = imagename.replace('.\\', "")
    splittedname = imagename.split('-')

    ## Make a dict of the data so we can easily see/use it
    data = {
        "imageName": imagename,
        "number": splittedname[1],
        "filter": splittedname[2],
        "file_format": imageformat,
        "success": success,
        "Alltags": labeledImage,
    }

    tagnumber = 0
    for tag in labeledImage:
        if tagnumber <= 4:
            stringTagNumber = f"tag{tagnumber+1}"
            stringTagNumberScore = f"tag{tagnumber+1}score"
            data[stringTagNumber] = labeledImage[tagnumber]['tag']
            data[stringTagNumberScore] = labeledImage[tagnumber]['score']
            tagnumber = tagnumber + 1

    ## Add the findings to the final list
    detectedImages.append(data)
    
    ## Done!
    scanned = scanned + 1

## When done, print the result
print(f"DONE. Writing results to csv file")

name = "output.csv"
with open(name,'w', newline='') as outfile:
    writer = DictWriter(outfile, ('imageName','number','filter','file_format','success','tag1','tag1score','tag2','tag2score','tag3','tag3score','tag4','tag4score','tag5','tag5score','Alltags'),delimiter=';')
    writer.writeheader()
    writer.writerows(detectedImages)

print(f"-----------------------")
print(f"IMAGE AMOUNT SCANNED: {scanned}")
print(f"TIMES SUCCESSFULL: {successTimes}")
print(f"TIMES UNSUCCESFULL: {failedTimes}")