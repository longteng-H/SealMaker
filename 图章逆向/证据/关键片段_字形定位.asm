
unpacked.exe:     file format pei-i386


Disassembly of section CODE:

005fd7f6 <CODE+0x1fc7f6>:
  5fd7f6:	50                   	push   %eax
  5fd7f7:	e8 34 a1 e0 ff       	call   0x407930
  5fd7fc:	8b 45 08             	mov    0x8(%ebp),%eax
  5fd7ff:	83 c0 f0             	add    $0xfffffff0,%eax
  5fd802:	e8 d1 21 00 00       	call   0x5ff9d8
  5fd807:	89 45 d0             	mov    %eax,-0x30(%ebp)
  5fd80a:	db 45 d0             	fildl  -0x30(%ebp)
  5fd80d:	d8 35 74 d9 5f 00    	fdivs  0x5fd974
  5fd813:	db 7d c4             	fstpt  -0x3c(%ebp)
  5fd816:	9b                   	fwait
  5fd817:	8b 45 08             	mov    0x8(%ebp),%eax
  5fd81a:	db 40 ec             	fildl  -0x14(%eax)
  5fd81d:	db 2d 78 d9 5f 00    	fldt   0x5fd978
  5fd823:	de c9                	fmulp  %st,%st(1)
  5fd825:	d8 35 84 d9 5f 00    	fdivs  0x5fd984
  5fd82b:	e8 70 53 e0 ff       	call   0x402ba0
  5fd830:	db 6d c4             	fldt   -0x3c(%ebp)
  5fd833:	de c9                	fmulp  %st,%st(1)
  5fd835:	8b 45 ec             	mov    -0x14(%ebp),%eax
  5fd838:	03 45 f4             	add    -0xc(%ebp),%eax
  5fd83b:	89 45 c0             	mov    %eax,-0x40(%ebp)
  5fd83e:	db 45 c0             	fildl  -0x40(%ebp)
  5fd841:	d8 35 74 d9 5f 00    	fdivs  0x5fd974
  5fd847:	de e1                	fsubp  %st,%st(1)
  5fd849:	db 7d b4             	fstpt  -0x4c(%ebp)
  5fd84c:	9b                   	fwait
  5fd84d:	8b 45 08             	mov    0x8(%ebp),%eax
  5fd850:	83 c0 f0             	add    $0xfffffff0,%eax
  5fd853:	e8 90 21 00 00       	call   0x5ff9e8
  5fd858:	89 45 b0             	mov    %eax,-0x50(%ebp)
  5fd85b:	db 45 b0             	fildl  -0x50(%ebp)
  5fd85e:	d8 35 74 d9 5f 00    	fdivs  0x5fd974
  5fd864:	db 7d a4             	fstpt  -0x5c(%ebp)
  5fd867:	9b                   	fwait
  5fd868:	8b 45 08             	mov    0x8(%ebp),%eax
  5fd86b:	db 40 ec             	fildl  -0x14(%eax)
  5fd86e:	db 2d 78 d9 5f 00    	fldt   0x5fd978
  5fd874:	de c9                	fmulp  %st,%st(1)
  5fd876:	d8 35 84 d9 5f 00    	fdivs  0x5fd984
  5fd87c:	e8 4f 53 e0 ff       	call   0x402bd0
  5fd881:	db 6d a4             	fldt   -0x5c(%ebp)
  5fd884:	de c9                	fmulp  %st,%st(1)
  5fd886:	db 6d b4             	fldt   -0x4c(%ebp)
  5fd889:	de e1                	fsubp  %st,%st(1)
  5fd88b:	e8 74 53 e0 ff       	call   0x402c04
  5fd890:	8b 55 08             	mov    0x8(%ebp),%edx
  5fd893:	8b 52 08             	mov    0x8(%edx),%edx
  5fd896:	89 02                	mov    %eax,(%edx)
  5fd898:	8b 45 08             	mov    0x8(%ebp),%eax
  5fd89b:	83 c0 f0             	add    $0xfffffff0,%eax
  5fd89e:	e8 35 21 00 00       	call   0x5ff9d8
  5fd8a3:	89 45 d0             	mov    %eax,-0x30(%ebp)
  5fd8a6:	db 45 d0             	fildl  -0x30(%ebp)
  5fd8a9:	d8 35 74 d9 5f 00    	fdivs  0x5fd974
  5fd8af:	db 7d c4             	fstpt  -0x3c(%ebp)
  5fd8b2:	9b                   	fwait
  5fd8b3:	8b 45 08             	mov    0x8(%ebp),%eax
  5fd8b6:	db 40 ec             	fildl  -0x14(%eax)
  5fd8b9:	db 2d 78 d9 5f 00    	fldt   0x5fd978
  5fd8bf:	de c9                	fmulp  %st,%st(1)
  5fd8c1:	d8 35 84 d9 5f 00    	fdivs  0x5fd984
  5fd8c7:	e8 04 53 e0 ff       	call   0x402bd0
  5fd8cc:	db 6d c4             	fldt   -0x3c(%ebp)
  5fd8cf:	de c9                	fmulp  %st,%st(1)
  5fd8d1:	8b 45 f0             	mov    -0x10(%ebp),%eax
  5fd8d4:	03 45 f8             	add    -0x8(%ebp),%eax
  5fd8d7:	89 45 c0             	mov    %eax,-0x40(%ebp)
  5fd8da:	db 45 c0             	fildl  -0x40(%ebp)
  5fd8dd:	d8                   	.byte 0xd8
  5fd8de:	35                   	.byte 0x35
  5fd8df:	74                   	.byte 0x74
