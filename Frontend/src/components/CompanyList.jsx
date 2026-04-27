
export default function CompanyList({ companies, selected, onSelect }) {
  return (
    <div className="company-list">
      <h3>Companies</h3>
      <ul>
        {companies.map(sym => (
          <li
            key={sym}
            className={sym === selected ? 'active' : ''}
            onClick={() => onSelect(sym)}
          >
            {sym}
          </li>
        ))}
      </ul>
    </div>
  );
}