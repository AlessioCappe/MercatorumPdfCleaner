import pymupdf
import hashlib
import sys
import os.path
import argparse

#variables
outPdfName = ''
convertToText = False
conversionDpi = 300

#input control
parser = argparse.ArgumentParser()
parser.add_argument("originalFile", help="File PDF sorgente")
parser.add_argument("destinationFile", nargs="?", default='', help="File PDF ripulito")

parser.add_argument("-r", "--ocr", action="store_true", help="Estrai il testo tramite OCR (se il PDF non ha testo selezionabile)")
parser.add_argument("-d", "--dpi", type=int, default=-1, help="Risoluzione a cui effettuare la conversione OCR")

args = parser.parse_args()

if not os.path.isfile(args.originalFile):
	print("File di origine non presente: " + args.originalFile)
	sys.exit()

if args.destinationFile != '':
    print("here?")
    outPdfName=args.destinationFile
    if not outPdfName.endswith(".pdf"):
        outPdfName = outPdfName + ".pdf"
else:
    outPdfName = os.path.splitext(os.path.basename(args.originalFile))[0] + "_clean.pdf"

if os.path.isfile(args.destinationFile):
    print("File di destinazione gia' presente: ", args.destinationFile)
    sys.exit()

if args.ocr:
    convertToText = True

if args.dpi > 0:
    conversionDpi = args.dpi
    #if dpi are set OCR is set
    convertToText = True

## FUNCTIONS

def cleanPageWatermark(page):
    backgroundImgHashes = [
		'668df6907cf9280c069050f61272dee4', 
		'd45621e8eefcf5de2cd97ff5e05a8470', 
		'3ffb92b2e0a0cf0998c9618c7217539b'
	]
    found = False

    for pdfImage in page.get_image_info(True, True):
        if hashlib.md5(pdfImage["digest"]).hexdigest() in backgroundImgHashes:
            #print("RefImg: " + str(pdfImage["xref"]))
            page.delete_image(pdfImage["xref"])
            found = True
    
    return found

def cleanPageCopyright(page):
    needles = ["22.04.1941/n", "uso personale"]
    found = False

    output = page.get_text("blocks")
    #print(output)
    #print("\n\n ----")
    for block in output:
        for needle in needles:
            if needle in block[4]:
                #print("Trovato in pagina " + str(pageNo))
                rect = pymupdf.Rect(block[0], block[1], block[2], block[3])
                page.draw_rect(rect, pymupdf.utils.getColor('white'), True)
                found = True
    
    return found
   
def analysePage(page):
	for pdfImages in page.get_image_info(True):
		print(pdfImages["digest"])
		print("Trovata immagine con hash: " + hashlib.md5(pdfImages["digest"]).hexdigest())
	
	return

def convertImgPageToTextPage(page, conversionDpi):
    pixMap = page.get_pixmap(dpi=conversionDpi)
    #pixMap.pdfocr_save("here.pdf", True, "ita")
    return pixMap.pdfocr_tobytes(True, "ita")

#NOT complete
def copyTextBlockBetweenPages(pageSource, pageDest, toPrint = False):
    textBlocks = pageSource.get_textpage().extractBLOCKS()
    for textBlock in textBlocks:
        #if toPrint:
            #print(textBlock)
        #print(textBlock[4])
        if textBlock[4].strip():
            #text is present
            rectBlock = pymupdf.Rect(textBlock[0]-10, textBlock[1], textBlock[2]+2.5, textBlock[3]+2.5)
            
            #print("altezza: ", rectBlock.height)
            pageDest.draw_rect(rectBlock)

            code = pageDest.insert_textbox(
                rectBlock,
                (f"{rectBlock.height:.2f}" + " - " + textBlock[4].strip()),
                #opacity = 0.0,
                #overlay = True
                #fontsize=rectBlock.height,   # approximate
                fontsize=(5)
                #fontname="helv",
                #render_mode=3,          # invisible text
            )

            if (toPrint and code<0):
                print(textBlock)
            #print("risultaot: " , code)

#NOT complete
def copyTextBlockBetweenPages2(pageSource, pageDest, toPrint = False):
    blocks = pageSource.get_text('dict')
    #blocks -> lines -> spans [text, bbox, size]

    for block in blocks["blocks"]:
        for line in block["lines"]:
            textLine = ''
            textHeight = -1
            for span in line["spans"]:
                textLine = textLine + " " + span["text"].strip()
                if(textHeight < 0):
                    textHeight = int(span["size"])
                    textHeight = textHeight-1

            print("Dimensione testo: ", textHeight)
            print("Testo: ", textLine)
        
            #print all the line
            wordBlock = pymupdf.Rect(line["bbox"][0], line["bbox"][1], line["bbox"][2], line["bbox"][3])
            code = pageDest.insert_textbox(
                wordBlock,
                textLine,
                #opacity = 0.0,
                #overlay = True
                #fontsize=rectBlock.height,   # approximate
                #fontsize=(int(span["size"])-2)
                fontsize=11
                #fontname="helv",
                #render_mode=3,          # invisible text
            )


    #end

### Workflow

#opening the file
doc = pymupdf.open(args.originalFile)

# DEBUG check the image in a single page to find the watermark img
#analysePage(doc[1])
#sys.exit()


if not convertToText:
    # OCR NOT REQUESTED!
    # Clean all pdf pages
    for pageNo in range(doc.page_count):
        print("Eseguo pag. ", (pageNo+1), " su ", doc.page_count)
        page = doc[pageNo]
        cleanPageCopyright(page)
        cleanPageWatermark(page)
        #print(output["bbox"])

    doc.save(outPdfName,garbage=4)
else:
    # OCR!
    outputDoc = pymupdf.open()
    for pageNo in range(doc.page_count):
        print("Eseguo pag. ", (pageNo+1), " su ", doc.page_count)
        page = doc[pageNo]
        cleanPageWatermark(page)

        ocrPage = pymupdf.open("pdf", convertImgPageToTextPage(page, conversionDpi))

        #if pageNo == 5:
            #print(ocrPage[0].get_text('dict'))
        #copyTextBlockBetweenPages(ocrPage[0], page, (pageNo==5))
        #copyTextBlockBetweenPages2(ocrPage[0], page)
            

        cleanPageCopyright(ocrPage[0])


        outputDoc.insert_pdf(ocrPage)

    #doc.save(outPdfName,garbage=4)
    outputDoc.save(outPdfName,garbage=4)


print("Generato il file: " + outPdfName)
sys.exit()
###