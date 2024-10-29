import pymupdf
import hashlib
import sys
import os.path

#input control
if len(sys.argv) < 2:
	print("Specificare il file pdf da elaborare")
	sys.exit()

if not os.path.isfile(sys.argv[1]):
	print("File non trovato\n")
	sys.exit()

outPdfName = ''

if len(sys.argv) <=2:
	outPdfName = os.path.splitext(os.path.basename(sys.argv[1]))[0] + "_clean.pdf"
if len(sys.argv) == 3:
	outPdfName = sys.argv[2]
	if not sys.argv[2].endswith(".pdf"):
		outPdfName = sys.argv[2] + ".pdf"

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
    needle = "L. 22.04.1941/n"
    found = False

    output = page.get_text("blocks")
    for block in output:
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

#opening the file
doc = pymupdf.open(sys.argv[1])

# check the image in a single page to find the watermark img
#analysePage(doc[1])
#sys.exit()

# Clean all pdf pages
for pageNo in range(doc.page_count):
    page = doc[pageNo]
    cleanPageCopyright(page)
    cleanPageWatermark(page)
    #print(output["bbox"])


doc.save(outPdfName,garbage=4)
print("Generato il file: " + outPdfName)
sys.exit()
