
unpacked.exe:     file format pei-i386


Disassembly of section CODE:

006e56a4 <CODE+0x2e46a4>:
  6e56a4:	55                   	push   %ebp
  6e56a5:	8b ec                	mov    %esp,%ebp
  6e56a7:	83 c4 94             	add    $0xffffff94,%esp
  6e56aa:	53                   	push   %ebx
  6e56ab:	56                   	push   %esi
  6e56ac:	57                   	push   %edi
  6e56ad:	89 55 fc             	mov    %edx,-0x4(%ebp)
  6e56b0:	8b f0                	mov    %eax,%esi
  6e56b2:	8d 5d a0             	lea    -0x60(%ebp),%ebx
  6e56b5:	db 2d 58 59 6e 00    	fldt   0x6e5958
  6e56bb:	e8 10 d5 d1 ff       	call   0x402bd0
  6e56c0:	dc 4d 18             	fmull  0x18(%ebp)
  6e56c3:	db 7d 94             	fstpt  -0x6c(%ebp)
  6e56c6:	9b db 2d 64 59 6e 00 	fldt   0x6e5964
  6e56cd:	e8 fe d4 d1 ff       	call   0x402bd0
  6e56d2:	db 6d 94             	fldt   -0x6c(%ebp)
  6e56d5:	de f1                	fdivp  %st,%st(1)
  6e56d7:	dd 5d f0             	fstpl  -0x10(%ebp)
  6e56da:	9b db 2d 58 59 6e 00 	fldt   0x6e5958
  6e56e1:	e8 ba d4 d1 ff       	call   0x402ba0
  6e56e6:	dc 4d 18             	fmull  0x18(%ebp)
  6e56e9:	dc 6d 28             	fsubrl 0x28(%ebp)
  6e56ec:	d9 1b                	fstps  (%ebx)
  6e56ee:	9b db 2d 58 59 6e 00 	fldt   0x6e5958
  6e56f5:	e8 d6 d4 d1 ff       	call   0x402bd0
  6e56fa:	dc 4d 18             	fmull  0x18(%ebp)
  6e56fd:	dc 6d 20             	fsubrl 0x20(%ebp)
  6e5700:	d9 5b 04             	fstps  0x4(%ebx)
  6e5703:	9b db 2d 64 59 6e 00 	fldt   0x6e5964
  6e570a:	e8 91 d4 d1 ff       	call   0x402ba0
  6e570f:	dc 4d f0             	fmull  -0x10(%ebp)
  6e5712:	dc 6d 28             	fsubrl 0x28(%ebp)
  6e5715:	d9 5b 08             	fstps  0x8(%ebx)
  6e5718:	9b                   	fwait
  6e5719:	8b 43 04             	mov    0x4(%ebx),%eax
  6e571c:	89 43 0c             	mov    %eax,0xc(%ebx)
  6e571f:	dd 45 28             	fldl   0x28(%ebp)
  6e5722:	d9 5b 10             	fstps  0x10(%ebx)
  6e5725:	9b dd 45 20          	fldl   0x20(%ebp)
  6e5729:	dc 65 18             	fsubl  0x18(%ebp)
  6e572c:	d9 5b 14             	fstps  0x14(%ebx)
  6e572f:	9b d9 05 70 59 6e 00 	flds   0x6e5970
  6e5736:	dc 4d 28             	fmull  0x28(%ebp)
  6e5739:	d8 63 08             	fsubs  0x8(%ebx)
  6e573c:	d9 5b 18             	fstps  0x18(%ebx)
  6e573f:	9b                   	fwait
  6e5740:	8b 43 0c             	mov    0xc(%ebx),%eax
  6e5743:	89 43 1c             	mov    %eax,0x1c(%ebx)
  6e5746:	d9 05 70 59 6e 00    	flds   0x6e5970
  6e574c:	dc 4d 28             	fmull  0x28(%ebp)
  6e574f:	d8 23                	fsubs  (%ebx)
  6e5751:	d9 5b 20             	fstps  0x20(%ebx)
  6e5754:	9b                   	fwait
  6e5755:	8b 43 04             	mov    0x4(%ebx),%eax
  6e5758:	89 43 24             	mov    %eax,0x24(%ebx)
  6e575b:	db 2d 58 59 6e 00    	fldt   0x6e5958
  6e5761:	e8 3a d4 d1 ff       	call   0x402ba0
  6e5766:	dc 4d f0             	fmull  -0x10(%ebp)
  6e5769:	dc 45 28             	faddl  0x28(%ebp)
  6e576c:	d9 5b 28             	fstps  0x28(%ebx)
  6e576f:	9b db 2d 58 59 6e 00 	fldt   0x6e5958
  6e5776:	e8 55 d4 d1 ff       	call   0x402bd0
  6e577b:	dc 4d f0             	fmull  -0x10(%ebp)
  6e577e:	dc 45 20             	faddl  0x20(%ebp)
  6e5781:	d9 5b 2c             	fstps  0x2c(%ebx)
  6e5784:	9b db 2d 64 59 6e 00 	fldt   0x6e5964
  6e578b:	e8 10 d4 d1 ff       	call   0x402ba0
  6e5790:	dc 4d 18             	fmull  0x18(%ebp)
  6e5793:	dc 45 28             	faddl  0x28(%ebp)
  6e5796:	d9 5b 30             	fstps  0x30(%ebx)
  6e5799:	9b db 2d 64 59 6e 00 	fldt   0x6e5964
  6e57a0:	e8 2b d4 d1 ff       	call   0x402bd0
  6e57a5:	dc 4d 18             	fmull  0x18(%ebp)
  6e57a8:	dc 45 20             	faddl  0x20(%ebp)
  6e57ab:	d9 5b 34             	fstps  0x34(%ebx)
  6e57ae:	9b dd 45 28          	fldl   0x28(%ebp)
  6e57b2:	d9 5b 38             	fstps  0x38(%ebx)
  6e57b5:	9b dd 45 20          	fldl   0x20(%ebp)
  6e57b9:	dc 45 f0             	faddl  -0x10(%ebp)
  6e57bc:	d9 5b 3c             	fstps  0x3c(%ebx)
  6e57bf:	9b                   	fwait
