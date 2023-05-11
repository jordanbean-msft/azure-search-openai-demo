import { Example } from "./Example";

import styles from "./Example.module.css";

export type ExampleModel = {
    text: string;
    value: string;
};

const EXAMPLES: ExampleModel[] = [
    {
        text: "Which insecticide manages sap-feeding insect pests?",
        value: "Which insecticide manages sap-feeding insect pests?"
    },
    { text: "My soil is wet & cold with temps less than 60 degrees Fahrenheit, which soybean diseases am I vulnerable to and which insecticide should I use?", value: "My soil is wet & cold with temps less than 60 degrees Fahrenheit, which soybean diseases am I vulnerable to and which insecticide should I use?" },
    { text: "I see brown lesions on my soybean roots, what should I do?", value: "I see brown lesions on my soybean roots, what should I do??" }
];

interface Props {
    onExampleClicked: (value: string) => void;
}

export const ExampleList = ({ onExampleClicked }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {EXAMPLES.map((x, i) => (
                <li key={i}>
                    <Example text={x.text} value={x.value} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
