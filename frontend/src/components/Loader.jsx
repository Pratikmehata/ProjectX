// src/components/Loader.jsx
import styled from "styled-components";

const Loader = ({ label = "Optimizing your build..." }) => (
  <StyledWrapper>
    <div className="loader" />
    {label && <p className="label">{label}</p>}
  </StyledWrapper>
);

const StyledWrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  gap: 28px;

  .label {
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    letter-spacing: 2px;
    color: #2a9d8f;
    text-transform: uppercase;
    animation: blink 1.2s ease-in-out infinite;
    margin: 0;
  }

  .loader {
    position: relative;
    width: 120px;
    height: 90px;
    margin: 0 auto;
  }

  .loader:before {
    content: "";
    position: absolute;
    bottom: 30px;
    left: 50px;
    height: 30px;
    width: 30px;
    border-radius: 50%;
    background: #2a9d8f;
    animation: loading-bounce 0.5s ease-in-out infinite alternate;
  }

  .loader:after {
    content: "";
    position: absolute;
    right: 0;
    top: 0;
    height: 7px;
    width: 45px;
    border-radius: 4px;
    box-shadow: 0 5px 0 #f2f2f2, -35px 50px 0 #f2f2f2, -70px 95px 0 #f2f2f2;
    animation: loading-step 1s ease-in-out infinite;
  }

  @keyframes loading-bounce {
    0%   { transform: scale(1, 0.7); }
    40%  { transform: scale(0.8, 1.2); }
    60%  { transform: scale(1, 1); }
    100% { bottom: 140px; }
  }

  @keyframes loading-step {
    0% {
      box-shadow:
        0 10px 0 rgba(0,0,0,0),
        0 10px 0 #f2f2f2,
        -35px 50px 0 #f2f2f2,
        -70px 90px 0 #f2f2f2;
    }
    100% {
      box-shadow:
        0 10px 0 #f2f2f2,
        -35px 50px 0 #f2f2f2,
        -70px 90px 0 #f2f2f2,
        -70px 90px 0 rgba(0,0,0,0);
    }
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }
`;

export default Loader;
