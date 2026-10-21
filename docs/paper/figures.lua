-- In the PDF a figure uses its vector PDF; the markdown on the web uses the SVG.
function Image(img)
  img.src = img.src:gsub('%.svg$', '.pdf')
  return img
end

-- An unnumbered chapter (Data availability, Acknowledgements, References) sets the running head too.
function Header(h)
  if h.level == 1 and h.classes:includes('unnumbered') then
    return {h, pandoc.RawBlock('latex', '\\markboth{' .. pandoc.utils.stringify(h.content) .. '}{}')}
  end
end

-- A short table is kept on one page: ask for room for its caption, header and
-- rows before it starts, so that it never begins at the foot of a page (a cell in a column of relative width wraps at about
-- 90 characters times that width). A longer table may break across pages,
-- with its header repeated.
function Table(tbl)
  if not FORMAT:match('latex') then return nil end
  -- rules and spacing, then the caption at about 95 characters a line
  local lines = 4 + math.ceil((utf8.len(pandoc.utils.stringify(tbl.caption.long)) or 0) / 95)
  local function count(rows)
    for _, row in ipairs(rows) do
      local tallest = 1
      for i, cell in ipairs(row.cells) do
        local w = tbl.colspecs[i] and tbl.colspecs[i][2]
        if type(w) == 'number' and w > 0 then
          local n = math.ceil((utf8.len(pandoc.utils.stringify(cell.contents)) or 0) / (90 * w))
          if n > tallest then tallest = n end
        end
      end
      lines = lines + tallest
    end
  end
  count(tbl.head.rows)
  for _, body in ipairs(tbl.bodies) do count(body.body) end
  count(tbl.foot.rows)
  if lines > 20 then return nil end
  return {pandoc.RawBlock('latex', '\\needspace{' .. lines .. '\\baselineskip}'), tbl}
end
