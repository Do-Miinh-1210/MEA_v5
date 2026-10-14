import fs from 'fs';

function removeLineCap(filePath) {
    if (!fs.existsSync(filePath)) return;
    let content = fs.readFileSync(filePath, 'utf8');
    
    // Replace combinations
    let newContent = content
        .replace(/,\s*line cap=round/g, '')
        .replace(/line cap=round,\s*/g, '')
        .replace(/line cap=round/g, '');
        
    if (content !== newContent) {
        fs.writeFileSync(filePath, newContent);
        console.log('Updated ' + filePath);
    }
}

removeLineCap('constants.tsx');
removeLineCap('services/geminiService.ts');
removeLineCap('check_bbt.ts');
removeLineCap('check_fill.ts');
removeLineCap('check_fill2.ts');
removeLineCap('check_lines.ts');
removeLineCap('count_stuff.ts');
removeLineCap('fix_bbt.ts');
removeLineCap('fix_geom_final.ts');
removeLineCap('fix_geometry.ts');
removeLineCap('fix_geometry2.ts');
