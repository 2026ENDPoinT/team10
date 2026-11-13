const chartText = value => typeof uiText === 'function' ? uiText(value) : value;
/*화면의 JavaScript 기능*/
/*화면의 JavaScript 기능*/

/* ------------------------------------------------------------------
 * 1. 다이나믹 아일랜드: 스크롤을 내리면 .scrolled 클래스를 붙여 살짝 작아지고 그림자가 짙어짐
 *    (위치 고정/따라오기 자체는 style.css 의 position: sticky 가 담당)
 * ------------------------------------------------------------------ */
(function () {
    const island = document.getElementById('island');
    if (!island) {
        return;
    }
    function onScroll() {
        island.classList.toggle('scrolled', window.scrollY > 10);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
})();

/* ------------------------------------------------------------------
 * 2. 성적 추이 그래프 (scores.html 에서만 동작)
 *    - window.SEMESTER_GPA : [{semester: '2026년 1학기', gpa: 3.8}, ...]  (scores.html 이 서버 값으로 채움)
 *    - window.OVERALL_GPA  : 전체 누적 평점평균 -> 가로 점선으로 표시
 *    과목을 등록/수정/삭제하면 서버가 다시 계산한 값으로 페이지가 새로 그려지므로 자동 반영됨
 * ------------------------------------------------------------------ */

// 한 해 안에서의 학기 순서 (1학기 -> 여름학기 -> 2학기 -> 겨울학기)
const TERM_ORDER = { '1학기': 1, '여름학기': 2, '2학기': 3, '겨울학기': 4 };

// "2026년 1학기" -> { year: 2026, term: '1학기' }
function parseSemester(label) {
    const m = /^(\d{4})년\s*(.+)$/.exec(label);
    return m ? { year: Number(m[1]), term: m[2] } : { year: 0, term: label };
}

// 시간 순서(과거 -> 최근)로 정렬한 새 배열 반환
function sortSemesters(list) {
    return list.slice().sort(function (a, b) {
        const pa = parseSemester(a.semester);
        const pb = parseSemester(b.semester);
        if (pa.year !== pb.year) {
            return pa.year - pb.year;
        }
        return (TERM_ORDER[pa.term] || 9) - (TERM_ORDER[pb.term] || 9);
    });
}

// SVG 요소 생성 도우미
function svgEl(tag, attrs, text) {
    const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const key in attrs) {
        el.setAttribute(key, attrs[key]);
    }
    if (text !== undefined) {
        el.textContent = text;
    }
    return el;
}

function drawGpaChart() {
    const chartBox = document.getElementById('gpa-chart');
    if (!chartBox) {
        return;   // 그래프 영역이 없는 페이지(퀴즈 등)에서는 아무것도 하지 않음
    }
    const emptyMsg = document.getElementById('gpa-chart-empty');
    const data = sortSemesters(window.SEMESTER_GPA || []);
    const overall = Number(window.OVERALL_GPA) || 0;

    chartBox.innerHTML = '';
    if (data.length === 0) {
        if (emptyMsg) { emptyMsg.hidden = false; }
        return;
    }
    if (emptyMsg) { emptyMsg.hidden = true; }

    // 그래프 크기 / 여백 (viewBox 기준, 실제 화면에서는 가로 100%로 자동 확대·축소)
    const W = 800, H = 340;
    const padL = 48, padR = 24, padT = 28, padB = 64;
    const MAX_GPA = 4.5;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;

    const yOf = function (v) { return padT + (1 - v / MAX_GPA) * plotH; };
    const xStart = padL + 50;
    const xEnd = W - padR - 50;
    const xOf = function (i) {
        return data.length === 1 ? padL + plotW / 2 : xStart + (xEnd - xStart) * i / (data.length - 1);
    };

    const svg = svgEl('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': chartText('학기별 성적 추이 그래프') });

    // 가로 눈금선 + 평점 눈금 숫자
    [0, 1, 2, 3, 4, 4.5].forEach(function (v) {
        svg.appendChild(svgEl('line', { x1: padL, x2: W - padR, y1: yOf(v), y2: yOf(v), class: 'gc-grid' }));
        svg.appendChild(svgEl('text', { x: padL - 10, y: yOf(v) + 4, class: 'gc-axis-text', 'text-anchor': 'end' }, String(v)));
    });

    // 전체 평균 가로선 (수치에 맞는 높이)
    const avgY = yOf(overall);
    svg.appendChild(svgEl('line', { x1: padL, x2: W - padR, y1: avgY, y2: avgY, class: 'gc-avg-line' }));
    svg.appendChild(svgEl('text', { x: W - padR - 4, y: avgY - 8, class: 'gc-avg-text', 'text-anchor': 'end' }, chartText('평균 ') + overall.toFixed(2)));

    // 학기별 평점 꺾은선
    if (data.length > 1) {
        const d = data.map(function (p, i) {
            return (i === 0 ? 'M' : 'L') + xOf(i) + ' ' + yOf(p.gpa);
        }).join(' ');
        svg.appendChild(svgEl('path', { d: d, class: 'gc-line' }));
    }

    // 점 + 평점 숫자 + 학기 이름
    const labelSize = data.length > 10 ? 10 : 12;
    data.forEach(function (p, i) {
        const x = xOf(i);
        const y = yOf(p.gpa);
        const parsed = parseSemester(p.semester);

        const circle = svgEl('circle', { cx: x, cy: y, r: 7, class: 'gc-point' });
        circle.appendChild(svgEl('title', {}, p.semester + ' : ' + p.gpa.toFixed(2) + ' / 4.5'));
        svg.appendChild(circle);

        svg.appendChild(svgEl('text', { x: x, y: y - 14, class: 'gc-value', 'text-anchor': 'middle' }, p.gpa.toFixed(2)));
        svg.appendChild(svgEl('text', { x: x, y: H - padB + 22, class: 'gc-axis-text', 'text-anchor': 'middle', 'font-size': labelSize }, parsed.year ? parsed.year + (window.UI_LANGUAGE === 'en' ? '' : '년') : ''));
        svg.appendChild(svgEl('text', { x: x, y: H - padB + 22 + labelSize + 4, class: 'gc-axis-text', 'text-anchor': 'middle', 'font-size': labelSize }, chartText(parsed.term)));
    });

    chartBox.appendChild(svg);
}

drawGpaChart();