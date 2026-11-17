
unpacked.exe:     file format pei-i386


Disassembly of section CODE:

005fe100 <CODE+0x1fd100>:
  5fe100:	04 00                	add    $0x0,%al
  5fe102:	7d 03                	jge    0x5fe107
  5fe104:	29 46 04             	sub    %eax,0x4(%esi)
  5fe107:	5e                   	pop    %esi
  5fe108:	5b                   	pop    %ebx
  5fe109:	5d                   	pop    %ebp
  5fe10a:	c3                   	ret
  5fe10b:	90                   	nop
  5fe10c:	55                   	push   %ebp
  5fe10d:	8b ec                	mov    %esp,%ebp
  5fe10f:	83 c4 f0             	add    $0xfffffff0,%esp
  5fe112:	53                   	push   %ebx
  5fe113:	56                   	push   %esi
  5fe114:	8b f0                	mov    %eax,%esi
  5fe116:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe119:	8b 40 fc             	mov    -0x4(%eax),%eax
  5fe11c:	8a 98 a0 00 00 00    	mov    0xa0(%eax),%bl
  5fe122:	84 db                	test   %bl,%bl
  5fe124:	75 0f                	jne    0x5fe135
  5fe126:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe129:	8b 40 fc             	mov    -0x4(%eax),%eax
  5fe12c:	80 b8 a8 00 00 00 00 	cmpb   $0x0,0xa8(%eax)
  5fe133:	74 33                	je     0x5fe168
  5fe135:	8d 4d f0             	lea    -0x10(%ebp),%ecx
  5fe138:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe13b:	8b d3                	mov    %ebx,%edx
  5fe13d:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe140:	8b 40 fc             	mov    -0x4(%eax),%eax
  5fe143:	8b 80 5c 01 00 00    	mov    0x15c(%eax),%eax
  5fe149:	8a 40 04             	mov    0x4(%eax),%al
  5fe14c:	e8 4f 48 fa ff       	call   0x5a29a0
  5fe151:	8b 45 f0             	mov    -0x10(%ebp),%eax
  5fe154:	01 06                	add    %eax,(%esi)
  5fe156:	8b 45 f4             	mov    -0xc(%ebp),%eax
  5fe159:	01 46 04             	add    %eax,0x4(%esi)
  5fe15c:	8b 45 f8             	mov    -0x8(%ebp),%eax
  5fe15f:	29 46 08             	sub    %eax,0x8(%esi)
  5fe162:	8b 45 fc             	mov    -0x4(%ebp),%eax
  5fe165:	29 46 0c             	sub    %eax,0xc(%esi)
  5fe168:	5e                   	pop    %esi
  5fe169:	5b                   	pop    %ebx
  5fe16a:	8b e5                	mov    %ebp,%esp
  5fe16c:	5d                   	pop    %ebp
  5fe16d:	c3                   	ret
  5fe16e:	8b c0                	mov    %eax,%eax
  5fe170:	55                   	push   %ebp
  5fe171:	8b ec                	mov    %esp,%ebp
  5fe173:	83 c4 dc             	add    $0xffffffdc,%esp
  5fe176:	53                   	push   %ebx
  5fe177:	56                   	push   %esi
  5fe178:	57                   	push   %edi
  5fe179:	8b f2                	mov    %edx,%esi
  5fe17b:	8d 7d dc             	lea    -0x24(%ebp),%edi
  5fe17e:	a5                   	movsl  %ds:(%esi),%es:(%edi)
  5fe17f:	a5                   	movsl  %ds:(%esi),%es:(%edi)
  5fe180:	a5                   	movsl  %ds:(%esi),%es:(%edi)
  5fe181:	a5                   	movsl  %ds:(%esi),%es:(%edi)
  5fe182:	89 4d fc             	mov    %ecx,-0x4(%ebp)
  5fe185:	8b f8                	mov    %eax,%edi
  5fe187:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe18a:	50                   	push   %eax
  5fe18b:	8b 4d fc             	mov    -0x4(%ebp),%ecx
  5fe18e:	8d 55 dc             	lea    -0x24(%ebp),%edx
  5fe191:	8b 47 04             	mov    0x4(%edi),%eax
  5fe194:	e8 3b f4 ff ff       	call   0x5fd5d4
  5fe199:	59                   	pop    %ecx
  5fe19a:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe19d:	50                   	push   %eax
  5fe19e:	8d 45 dc             	lea    -0x24(%ebp),%eax
  5fe1a1:	e8 66 ff ff ff       	call   0x5fe10c
  5fe1a6:	59                   	pop    %ecx
  5fe1a7:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe1aa:	8b 40 fc             	mov    -0x4(%eax),%eax
  5fe1ad:	8b 88 60 01 00 00    	mov    0x160(%eax),%ecx
  5fe1b3:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe1b6:	8b 40 fc             	mov    -0x4(%eax),%eax
  5fe1b9:	8b 90 80 00 00 00    	mov    0x80(%eax),%edx
  5fe1bf:	8b 47 04             	mov    0x4(%edi),%eax
  5fe1c2:	e8 65 2c 00 00       	call   0x600e2c
  5fe1c7:	8b d8                	mov    %eax,%ebx
  5fe1c9:	8b f3                	mov    %ebx,%esi
  5fe1cb:	83 e6 7f             	and    $0x7f,%esi
  5fe1ce:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe1d1:	8b 40 fc             	mov    -0x4(%eax),%eax
  5fe1d4:	0f af b0 60 01 00 00 	imul   0x160(%eax),%esi
  5fe1db:	8b c6                	mov    %esi,%eax
  5fe1dd:	b9 68 01 00 00       	mov    $0x168,%ecx
  5fe1e2:	99                   	cltd
  5fe1e3:	f7 f9                	idiv   %ecx
  5fe1e5:	8b c2                	mov    %edx,%eax
  5fe1e7:	05 68 01 00 00       	add    $0x168,%eax
  5fe1ec:	b9 68 01 00 00       	mov    $0x168,%ecx
  5fe1f1:	99                   	cltd
  5fe1f2:	f7 f9                	idiv   %ecx
  5fe1f4:	8b f2                	mov    %edx,%esi
  5fe1f6:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe1f9:	50                   	push   %eax
  5fe1fa:	8d 45 f4             	lea    -0xc(%ebp),%eax
  5fe1fd:	50                   	push   %eax
  5fe1fe:	8d 45 ec             	lea    -0x14(%ebp),%eax
  5fe201:	50                   	push   %eax
  5fe202:	8b ce                	mov    %esi,%ecx
  5fe204:	8d 55 dc             	lea    -0x24(%ebp),%edx
  5fe207:	8b 47 04             	mov    0x4(%edi),%eax
  5fe20a:	e8 8d f7 ff ff       	call   0x5fd99c
  5fe20f:	59                   	pop    %ecx
  5fe210:	8b c7                	mov    %edi,%eax
  5fe212:	e8 9d 54 f3 ff       	call   0x5336b4
  5fe217:	b2 01                	mov    $0x1,%dl
  5fe219:	e8 4a f0 e2 ff       	call   0x42d268
  5fe21e:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe221:	50                   	push   %eax
  5fe222:	8d 45 f4             	lea    -0xc(%ebp),%eax
  5fe225:	50                   	push   %eax
  5fe226:	85 f6                	test   %esi,%esi
  5fe228:	0f 95 c0             	setne  %al
  5fe22b:	50                   	push   %eax
  5fe22c:	8d 4d ec             	lea    -0x14(%ebp),%ecx
  5fe22f:	8d 55 dc             	lea    -0x24(%ebp),%edx
  5fe232:	8b c7                	mov    %edi,%eax
  5fe234:	e8 d3 f9 ff ff       	call   0x5fdc0c
  5fe239:	59                   	pop    %ecx
  5fe23a:	8b 45 08             	mov    0x8(%ebp),%eax
  5fe23d:	50                   	push   %eax
  5fe23e:	8d                   	.byte 0x8d
  5fe23f:	55                   	push   %ebp
