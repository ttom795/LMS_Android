import json,sys,pefile,capstone
pe=pefile.PE(sys.argv[1]);img=pe.get_memory_mapped_image();B=pe.OPTIONAL_HEADER.ImageBase
d=json.load(open(sys.argv[2]))
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
cov=bytearray(len(img))
for f,bl in d["functions"].items():
  pass
